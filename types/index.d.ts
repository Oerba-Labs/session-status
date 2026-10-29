export type LaneState = 'open' | 'blocked' | 'needs-input' | 'closed'

export type Lane = { name: string; state: LaneState; detail: string }

export type Summary = { topic: string; now: string }

declare module 'claude-code' {
  interface PluginState {
    'session-status': {
      summary: Summary | null
      doing: string | null
      attached: string[]
      lanes: Lane[]
    }
  }
}
