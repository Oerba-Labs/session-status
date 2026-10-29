# session-status

A Claude Code mod that keeps a short status above the prompt: what the conversation is about,
what Claude is doing right now, and the [lanekit](https://github.com/Oerba-Labs/lanekit) lanes
the session has touched, each with its state.

```
◆ Status band for the terminal  ·  now: Land the login lane
  ! login-page     needs you  gate green: waiting for your yes to land
  ✕ search-index   blocked    gate failed at 3f2a9c1
  ● docs-refresh   open       2 ahead, uncommitted changes
  ✓ old-cleanup    closed     landed
```

The same story is put in one line on the status line, for a layout that does not draw the band.

## What it does

- **The summary.** While Claude works, "now" is the step it is taking (a command's description,
  the file it edits, the agent it starts). When a turn ends, Haiku reads the newest part of the
  conversation and writes the topic and what is in hand, in a few words. That is one small Haiku
  call per turn, through the session's own client.
- **The lanes.** A lane is attached to the session when a tool call names it: a `lane <verb> <name>`
  command, a lanekit tool, or a path inside the lane's folder, from the main conversation or any
  subagent. A session that runs inside a lane attaches that lane by itself.
- **The states**, read from git and lanekit's gate records every minute and after any lane activity,
  changing nothing:
  - **needs you**: its gate passed at its current commit with nothing uncommitted; it waits to land.
  - **blocked**: part-way through a rebase or merge, its gate failed at its current commit, or its
    folder is gone while its branch holds commits the integration branch has not.
  - **open**: being worked on.
  - **closed**: landed or dropped.

It needs `git` and `python3` on the machine, and does nothing with lanes in a repository without a
`lane.config.json`.

## Install

At the prompt of a Claude Code terminal session:

```
/plugin install session-status --marketplace Oerba-Labs/session-status
```

Answer `y` to add the marketplace, then pick a scope.

From a shell:

```
claude plugin install session-status --marketplace Oerba-Labs/session-status
```

In the desktop app, where `/plugin` does not run: click + next to the prompt box, then Plugins,
Add marketplace with `Oerba-Labs/session-status`, then Add plugin.
