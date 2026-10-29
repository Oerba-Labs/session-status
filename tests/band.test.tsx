import { expect, test } from 'claude-code/testing'

const BAND = {
  plugin: 'session-status',
  component: 'AbovePrompt',
  requestId: 'above-prompt',
  props: {
    hasSurvey: false,
    isWorking: false,
    maxRows: 12,
    bodyColumns: 100,
    scroll: { offset: 0, bodyRows: 11 },
    view: {},
  },
} as const

const HELPER = JSON.stringify({
  repo: '/w/project',
  own: null,
  lanes: [
    { name: 'login-page', state: 'needs-input', detail: 'gate green: waiting for your yes to land', known: true },
    { name: 'docs-refresh', state: 'open', detail: '2 ahead', known: true },
    { name: 'not-a-lane', state: 'closed', detail: 'dropped or swept', known: false },
  ],
})

test('a lane a command names is attached and drawn with its state', async ($, on) => {
  const asked: string[][] = []
  on('process.run', (_, e) => {
    asked.push([...e.argv])
    return { value: { exitCode: 0, stdout: HELPER, stderr: '' } }
  })
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('tool.call', () => ({ result: {} }))
  on('clock.every', () => ({ value: undefined }))
  on('session.cwd', () => ({ value: '/w/project' }))
  on('ui.log', () => ({ value: undefined }))

  await $.session.start({ cwd: '/w/project', surface: 'terminal', isInteractive: true })
  await $.tool.call({ tool: 'Bash', command: 'lane land login-page', description: 'Land the login lane' })

  // The refresh runs beside the call, not inside it: give it a moment to answer.
  for (let i = 0; i < 200 && !asked.some(argv => argv.includes('login-page')); i += 1) {
    await new Promise(resolve => setTimeout(resolve, 5))
  }
  expect(asked.some(argv => argv.includes('login-page'))).toBe(true)

  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...BAND, surface })
    expect(await ui.find({ type: 'Text', text: /login-page/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /needs you/ })).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /not-a-lane/ })).toBeUndefined()
    await ui.unmount()
  }
})
