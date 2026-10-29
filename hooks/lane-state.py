"""Where each named lane stands, for the session-status band: one JSON object on stdout.

    python3 -I lane-state.py <a folder inside the repository or one of its lanes> [<lane>...]

Reads only: git's view of the main checkout and of each lane's folder, and lanekit's gate
records in <main>/.lanekit/runs. It changes nothing, so it is safe to run every minute.

The states, in lanekit's own terms:
  closed       landed (its commits are on the integration branch) or dropped (no folder, no branch)
  blocked      part-way through a rebase or merge, its last gate failed at its current commit,
               or its folder is gone while its branch holds commits the integration branch has not
  needs-input  its gate passed at its current commit with nothing uncommitted: it waits for a
               person's yes to land
  open         anything else: being worked on
"""
import json
import os
import re
import subprocess
import sys

NAME = re.compile(r"[a-z0-9][a-z0-9._-]{0,99}\Z")


def git(cwd, *args):
    done = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True)
    return done.stdout.strip() if done.returncode == 0 else None


def newest_runs(repo, most=300):
    folder = os.path.join(repo, ".lanekit", "runs")
    try:
        names = sorted((n for n in os.listdir(folder) if n.endswith(".json")), reverse=True)[:most]
    except OSError:
        return []
    runs = []
    for name in names:
        try:
            with open(os.path.join(folder, name), encoding="utf-8") as f:
                run = json.load(f)
        except (OSError, ValueError):
            continue
        if isinstance(run, dict) and run.get("kind") != "full":
            runs.append(run)
    return runs


def state_of(repo, base, first_parent, runs, name):
    path = os.path.join(os.path.dirname(repo), f"{os.path.basename(repo)}-{name}")
    branch = git(repo, "rev-parse", "--verify", "-q", f"refs/heads/{name}")
    ahead_text = git(repo, "rev-list", "--count", f"{base}..refs/heads/{name}") if branch else None
    ahead = int(ahead_text) if ahead_text and ahead_text.isdigit() else 0

    if not os.path.isdir(path):
        if branch is None:
            return "closed", "dropped or swept", False
        if ahead == 0:
            return "closed", "landed", True
        return "blocked", f"folder gone, {ahead} commits not on {base}", True

    git_dir = git(path, "rev-parse", "--absolute-git-dir")
    if git_dir:
        for marker, what in (("rebase-merge", "rebase"), ("rebase-apply", "rebase"), ("MERGE_HEAD", "merge")):
            if os.path.exists(os.path.join(git_dir, marker)):
                return "blocked", f"part-way through a {what}", True

    head = git(path, "rev-parse", "HEAD")
    dirty = bool(git(path, "status", "--porcelain"))
    if ahead == 0 and not dirty:
        if head in first_parent:
            return "open", "nothing committed yet", True
        return "closed", "landed, folder not swept", True

    last = next((r for r in runs if r.get("worktree") == path or (not r.get("worktree") and r.get("branch") == name)), None)
    if last and last.get("sha") == head:
        if last.get("result") == "failed":
            return "blocked", f"gate failed at {head[:7]}", True
        if last.get("result") == "passed" and not dirty and not last.get("narrowed"):
            return "needs-input", "gate green: waiting for your yes to land", True

    aside = git(repo, "config", "--get", f"branch.{name}.lanekitaside")
    said = ([f"{ahead} ahead"] if ahead else []) +(["uncommitted changes"] if dirty else []) + (["set aside"] if aside else [])
    return "open", ", ".join(said), True


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "no folder given"}))
        return
    here = os.path.abspath(sys.argv[1])
    common = git(here, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if common is None:
        print(json.dumps({"error": "not inside a git checkout", "lanes": []}))
        return
    repo = os.path.dirname(common)
    if not os.path.isfile(os.path.join(repo, "lane.config.json")):
        print(json.dumps({"error": "this repository has no lanes", "lanes": []}))
        return
    try:
        with open(os.path.join(repo, "lane.config.json"), encoding="utf-8") as f:
            base = json.load(f).get("integrationBranch") or "main"
    except (OSError, ValueError):
        base = "main"

    # The folder the session itself is in, when that folder is a lane.
    top = git(here, "rev-parse", "--show-toplevel")
    prefix = f"{os.path.basename(repo)}-"
    own = None
    if top and top != repo and os.path.dirname(top) == os.path.dirname(repo) and os.path.basename(top).startswith(prefix):
        own = os.path.basename(top)[len(prefix):]

    names = [n for n in dict.fromkeys(([own] if own else []) + sys.argv[2:]) if NAME.match(n)]
    first_parent = set((git(repo, "rev-list", "--first-parent", "-n2000", base) or "").split())
    runs = newest_runs(repo)

    lanes = []
    for name in names:
        state, detail, known = state_of(repo, base, first_parent, runs, name)
        lanes.append({"name": name, "state": state, "detail": detail, "known": known})
    print(json.dumps({"repo": repo, "own": own, "lanes": lanes}))


if __name__ == "__main__":
    main()
