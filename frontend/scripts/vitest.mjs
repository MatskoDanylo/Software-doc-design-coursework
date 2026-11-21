// Vitest 5 loads itself twice on Windows when cwd has a lowercase drive letter (vitest-dev/vitest#11872).
import { spawnSync } from 'node:child_process'
import { realpathSync } from 'node:fs'
import { join } from 'node:path'

const cwd = realpathSync.native(process.cwd())
const cli = join(cwd, 'node_modules', 'vitest', 'vitest.mjs')
const { status } = spawnSync(process.execPath, [cli, ...process.argv.slice(2)], { cwd, stdio: 'inherit' })

process.exit(status ?? 1)
