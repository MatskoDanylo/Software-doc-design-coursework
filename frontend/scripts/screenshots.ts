// Screenshots of the UI for the coursework report.
//
// Needs the backend on :8000 and `npm run dev` on :5173 with demo data
// (`python -m app.seed --demo-activity` and `python -m app.tools.demo_media`).
// Run: npm run screenshots   →   PNG files in docs/screenshots/
//
// Environment overrides: APP_URL, API_URL, ADMIN_EMAIL, ADMIN_PASSWORD, PREMIUM_EMAIL,
// SCREENSHOT_CHANNEL (chromium by default, or chrome | msedge), SCREENSHOT_ONLY (comma-separated name fragments).
import { existsSync, mkdirSync, readFileSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium, type Browser, type Locator, type Page } from 'playwright'

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..')
const OUT_DIR = join(ROOT, 'docs', 'screenshots')
const APP_URL = (process.env.APP_URL ?? 'http://localhost:5173').replace(/\/+$/, '')
const API_URL = (process.env.API_URL ?? 'http://localhost:8000').replace(/\/+$/, '')
const DESKTOP = { width: 1440, height: 900 }
const MOBILE = { width: 375, height: 812 }
const DEMO_PASSWORD = 'demo12345'
const FREE_USER = { email: 'demo.user05@example.com', password: DEMO_PASSWORD }
const HEADER_OFFSET = 96
const ONLY = (process.env.SCREENSHOT_ONLY ?? '').split(',').map((part) => part.trim()).filter(Boolean)

interface Credentials {
  email: string
  password: string
}

interface TokenPair {
  access_token: string
  refresh_token: string
}

interface TitleCard {
  id: number
  name: string
  kind: 'movie' | 'series'
}

interface TitlePage {
  items: TitleCard[]
}

interface Genre {
  id: number
  name: string
}

interface Account {
  id: number
  email: string
  subscription: { plan_code: 'free' | 'premium' }
}

// ---------------------------------------------------------------- configuration

function readDotEnv(path: string): Record<string, string> {
  if (!existsSync(path)) return {}
  const entries = readFileSync(path, 'utf8')
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith('#') && line.includes('='))
    .map((line) => {
      const at = line.indexOf('=')
      return [line.slice(0, at).trim(), line.slice(at + 1).trim().replace(/^["']|["']$/g, '')]
    })
  return Object.fromEntries(entries)
}

const backendEnv = readDotEnv(join(ROOT, 'backend', '.env'))
const ADMIN: Credentials = {
  email: process.env.ADMIN_EMAIL ?? backendEnv.ADMIN_EMAIL ?? 'admin@example.com',
  password: process.env.ADMIN_PASSWORD ?? backendEnv.ADMIN_PASSWORD ?? 'admin12345',
}

// ---------------------------------------------------------------- API helpers

async function api<T>(path: string, options: { method?: string; token?: string; body?: unknown } = {}): Promise<T> {
  const { method = 'GET', token, body } = options
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (token) headers.Authorization = `Bearer ${token}`
  const response = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (!response.ok) throw new Error(`${method} ${path} → ${response.status}: ${await response.text()}`)
  return (response.status === 204 ? undefined : await response.json()) as T
}

async function login(credentials: Credentials, hint: string): Promise<TokenPair> {
  try {
    return await api<TokenPair>('/api/auth/login', { method: 'POST', body: credentials })
  } catch (error) {
    throw new Error(`Не вдалося увійти як ${credentials.email}. ${hint}\n${String(error)}`)
  }
}

async function ensureReachable(): Promise<void> {
  const check = async (url: string, what: string, how: string) => {
    try {
      await fetch(url)
    } catch {
      throw new Error(`${what} недоступний (${url}). ${how}`)
    }
  }
  await check(`${API_URL}/api/plans`, 'Бекенд', 'Запустіть: python -m uvicorn app.main:app --reload (з backend/).')
  await check(APP_URL, 'Фронтенд', 'Запустіть: npm run dev (з frontend/).')
}

async function findMovieWithVideo(token: string): Promise<TitleCard> {
  const page = await api<TitlePage>('/api/titles?kind=movie&sort=popularity&page_size=50', { token })
  for (const title of page.items) {
    const response = await fetch(`${API_URL}/api/titles/${title.id}/playback`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (response.ok) return title
  }
  throw new Error('Немає жодного фільму з готовим відео. Запустіть: python -m app.tools.demo_media (з backend/).')
}

async function findPremiumUser(adminToken: string): Promise<Credentials> {
  if (process.env.PREMIUM_EMAIL) return { email: process.env.PREMIUM_EMAIL, password: DEMO_PASSWORD }
  const users = await api<Account[]>('/api/admin/users?limit=100', { token: adminToken })
  const premium = users.find((user) => user.email.startsWith('demo.') && user.subscription.plan_code === 'premium')
  if (premium) return { email: premium.email, password: DEMO_PASSWORD }

  const fallback = users.find((user) => user.email === 'demo.user01@example.com')
  if (!fallback) throw new Error('Демо-користувачів немає. Запустіть: python -m app.seed --demo-activity (з backend/).')
  console.warn(`! Жоден демо-користувач не має Преміуму — видаю його ${fallback.email} на 30 днів`)
  await api(`/api/admin/users/${fallback.id}/subscription`, {
    method: 'POST',
    token: adminToken,
    body: { action: 'grant', days: 30 },
  })
  return { email: fallback.email, password: DEMO_PASSWORD }
}

async function ensureFavorites(token: string): Promise<void> {
  const favorites = await api<{ total: number }>('/api/favorites', { token })
  if (favorites.total > 0) return
  const popular = await api<TitlePage>('/api/titles?sort=popularity&page_size=4', { token })
  for (const title of popular.items) await api(`/api/favorites/${title.id}`, { method: 'POST', token })
}

// ---------------------------------------------------------------- browser helpers

/** Chromium from Playwright by default; SCREENSHOT_CHANNEL=chrome|msedge uses an installed browser instead. */
async function launchBrowser(): Promise<Browser> {
  const args = ['--autoplay-policy=no-user-gesture-required']
  const channel = process.env.SCREENSHOT_CHANNEL
  try {
    const browser = await chromium.launch(channel && channel !== 'chromium' ? { channel, args } : { args })
    const probe = await browser.newPage()
    const h264 = await probe.evaluate(() => MediaSource.isTypeSupported('video/mp4; codecs="avc1.64001f,mp4a.40.2"'))
    await probe.context().close()
    if (!h264) console.warn('! Браузер не підтримує H.264: спробуйте SCREENSHOT_CHANNEL=chrome')
    console.log(`Браузер: ${channel ?? 'chromium'}`)
    return browser
  } catch (error) {
    throw new Error(`Не вдалося запустити браузер. Виконайте: npx playwright install chromium\n${String(error)}`)
  }
}

const HIDE_TOASTS = `
  document.addEventListener('DOMContentLoaded', () => {
    const style = document.createElement('style')
    style.textContent = 'section[aria-label="Повідомлення"] { display: none !important }'
    document.head.append(style)
  })
`

async function openPage(browser: Browser, tokens: TokenPair | null, mobile = false): Promise<Page> {
  const context = await browser.newContext({
    viewport: mobile ? MOBILE : DESKTOP,
    deviceScaleFactor: 2,
    isMobile: mobile,
    hasTouch: mobile,
    locale: 'uk-UA',
    timezoneId: 'Europe/Kyiv',
    colorScheme: 'dark',
    reducedMotion: 'reduce',
  })
  await context.addInitScript(HIDE_TOASTS)
  if (tokens) {
    // Refresh tokens are stateless JWTs, so restoring the same one on every page load is safe.
    await context.addInitScript((token) => localStorage.setItem('cinema.refresh_token', token), tokens.refresh_token)
  }
  return context.newPage()
}

/** Waits until requests are done, no spinner/skeleton is visible and on-screen images are decoded. */
async function settle(page: Page): Promise<void> {
  await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => undefined)
  try {
    await page.waitForFunction(
      () => {
        const onScreen = (element: Element) => {
          const rect = element.getBoundingClientRect()
          return rect.width > 0 && rect.height > 0 && rect.bottom > 0 && rect.top < window.innerHeight
        }
        const busy = [...document.querySelectorAll('.animate-spin, .animate-pulse, [aria-busy="true"]')].some(onScreen)
        const loadingText = /Завантаження…|Перевіряємо|Готуємо файл/.test(document.body.innerText)
        const images = [...document.images].filter(onScreen).every((image) => image.complete && image.naturalWidth > 0)
        return !busy && !loadingText && images
      },
      undefined,
      { timeout: 30_000, polling: 250 },
    )
  } catch {
    throw new Error(`Сторінка ${page.url()} не завершила завантаження за 30 с (видно спінер або скелетон)`)
  }
  await page.evaluate(() => document.fonts.ready.then(() => undefined))
  await page.waitForTimeout(700)
}

async function scrollToTop(locator: Locator): Promise<void> {
  await locator.first().evaluate((element, offset) => {
    window.scrollTo({ top: element.getBoundingClientRect().top + window.scrollY - offset, behavior: 'instant' })
  }, HEADER_OFFSET)
}

async function waitForVideo(page: Page, selector: string, minSeconds: number): Promise<void> {
  try {
    await page.waitForFunction(
      ({ selector, minSeconds }) => {
        const video = document.querySelector<HTMLVideoElement>(selector)
        return video !== null && video.readyState >= 2 && video.currentTime >= minSeconds
      },
      { selector, minSeconds },
      { timeout: 30_000, polling: 200 },
    )
  } catch {
    throw new Error(`Відео (${selector}) не почало відтворюватися на ${page.url()}. Перевірте, що відео готове.`)
  }
  await page.evaluate((selector) => document.querySelector<HTMLVideoElement>(selector)?.pause(), selector)
}

let taken = 0

async function shot(page: Page, name: string): Promise<void> {
  if (ONLY.length > 0 && !ONLY.some((part) => name.includes(part))) return
  await page.screenshot({ path: join(OUT_DIR, `${name}.png`), animations: 'disabled', caret: 'hide' })
  taken += 1
  console.log(`  ✓ ${name}.png`)
}

async function goto(page: Page, path: string): Promise<void> {
  await page.goto(`${APP_URL}${path}`, { waitUntil: 'domcontentloaded' })
}

// ---------------------------------------------------------------- scenarios

async function guestScreens(browser: Browser): Promise<void> {
  console.log('Гість')
  const genres = await api<Genre[]>('/api/genres')
  const genre = genres.find((item) => item.name === 'Драма') ?? genres[0]
  const filters = `?genre=${genre.id}&year_from=1990&sort=rating`

  const page = await openPage(browser, null)
  await goto(page, `/catalog${filters}`)
  await settle(page)
  await shot(page, '02-catalog-filters')
  await page.context().close()

  const mobile = await openPage(browser, null, true)
  await goto(mobile, '/catalog')
  await settle(mobile)
  await shot(mobile, '23-mobile-catalog-375')
  await mobile.context().close()
}

async function freeUserScreens(browser: Browser, movie: TitleCard): Promise<void> {
  console.log(`Безкоштовний план: ${FREE_USER.email}`)
  const tokens = await login(FREE_USER, 'Запустіть: python -m app.seed --demo-activity (з backend/).')
  const me = await api<Account>('/api/users/me', { token: tokens.access_token })
  if (me.subscription.plan_code !== 'free') {
    console.warn(`! ${FREE_USER.email} зараз на Преміумі — знімки «Безкоштовного» плану будуть без реклами`)
  }
  await ensureFavorites(tokens.access_token)
  const page = await openPage(browser, tokens)

  await goto(page, '/')
  await settle(page)
  await scrollToTop(page.getByRole('heading', { name: 'Рекомендовано для вас' }))
  await settle(page)
  await shot(page, '01-home-recommendations')

  await goto(page, `/titles/${movie.id}`)
  await settle(page)
  await page.getByRole('heading', { name: 'Схожі' }).scrollIntoViewIfNeeded()
  await page.evaluate(() => window.scrollBy({ top: 120, behavior: 'instant' }))
  await settle(page)
  await shot(page, '03-title-similar')

  await goto(page, `/watch/${movie.id}`)
  const ad = page.getByRole('region', { name: 'Реклама' })
  if (await ad.waitFor({ timeout: 15_000 }).then(() => true, () => false)) {
    await waitForVideo(page, 'section[aria-label="Реклама"] video', 1.5)
  } else {
    console.warn('! Реклами немає (немає media/ads/preroll або користувач на Преміумі)')
    await waitForVideo(page, 'video[aria-label="Відеоплеєр"]', 1.5)
  }
  await page.waitForTimeout(300)
  await shot(page, '04-player-free-ad')

  await goto(page, '/favorites')
  await settle(page)
  await shot(page, '06-favorites')

  await goto(page, '/pricing')
  await settle(page)
  await shot(page, '08-pricing')
  await page.context().close()
}

async function premiumUserScreens(browser: Browser, credentials: Credentials, movie: TitleCard): Promise<void> {
  console.log(`Преміум: ${credentials.email}`)
  const tokens = await login(credentials, 'Перевірте пароль демо-користувача або задайте PREMIUM_EMAIL.')
  const page = await openPage(browser, tokens)

  await goto(page, `/watch/${movie.id}`)
  await waitForVideo(page, 'video[aria-label="Відеоплеєр"]', 1.5)
  const quality = page.getByLabel('Якість')
  const heights = await quality.locator('option').evaluateAll((options) =>
    options.map((option) => (option as HTMLOptionElement).value).filter((value) => value !== 'auto'),
  )
  if (heights.length > 0) await quality.selectOption(heights[0])
  await page.waitForTimeout(800)
  await quality.focus()
  await shot(page, '05-player-premium-quality')

  await goto(page, '/profile')
  await settle(page)
  await scrollToTop(page.getByRole('heading', { name: 'Підписка' }))
  await settle(page)
  await shot(page, '07-profile-subscription')
  await page.context().close()
}

async function payAndCapture(
  page: Page,
  token: string,
  outcome: string,
  heading: string,
  name: string,
  checkoutShot?: string,
): Promise<void> {
  const { payment_id } = await api<{ payment_id: number }>('/api/billing/checkout', {
    method: 'POST',
    token,
    body: { plan_code: 'premium' },
  })
  await goto(page, `/checkout/${payment_id}`)
  await settle(page)
  if (checkoutShot) await shot(page, checkoutShot)
  await page.getByRole('radio', { name: outcome }).check()
  await page.getByRole('button', { name: 'Оплатити' }).click()
  await page.getByRole('heading', { name: heading }).waitFor({ timeout: 15_000 })
  await settle(page)
  await shot(page, name)
}

async function paymentScreens(browser: Browser): Promise<void> {
  const credentials = { email: `screens.${Date.now()}@example.com`, password: DEMO_PASSWORD }
  console.log(`Оплата: новий користувач ${credentials.email}`)
  await api('/api/auth/register', { method: 'POST', body: { ...credentials, display_name: 'Олена Коваль' } })
  const tokens = await login(credentials, '')
  const page = await openPage(browser, tokens)

  await payAndCapture(page, tokens.access_token, 'Відхилено банком', 'Оплату відхилено', '10-payment-failed', '09-checkout-outcome')
  await payAndCapture(page, tokens.access_token, 'Очікує підтвердження', 'Оплата очікує підтвердження', '11-payment-pending')
  await payAndCapture(page, tokens.access_token, 'Успішна оплата', 'Оплату прийнято', '12-payment-success')

  await goto(page, '/')
  await settle(page)
  await page.getByRole('button', { name: /^Сповіщення/ }).click()
  await page.getByRole('heading', { name: 'Сповіщення' }).waitFor()
  await settle(page)
  await shot(page, '13-notifications')
  await page.context().close()
}

async function adminScreens(browser: Browser, tokens: TokenPair, movie: TitleCard): Promise<void> {
  console.log(`Адміністратор: ${ADMIN.email}`)
  const page = await openPage(browser, tokens)

  const pages: [string, string][] = [
    ['/admin', '14-admin-dashboard'],
    ['/admin/titles', '15-admin-titles'],
    [`/admin/titles/${movie.id}`, '16-admin-title-edit'],
  ]
  for (const [path, name] of pages) {
    await goto(page, path)
    await settle(page)
    await shot(page, name)
  }

  await scrollToTop(page.getByRole('heading', { name: 'Відео', exact: true }))
  await page.getByLabel('Файл відео').setInputFiles({
    name: 'trailer-1080p.mp4',
    mimeType: 'video/mp4',
    buffer: Buffer.from('demo'),
  })
  await settle(page)
  await shot(page, '17-admin-video-upload')

  const rest: [string, string][] = [
    ['/admin/payments', '18-admin-payments'],
    ['/admin/reports?tab=popular', '19-admin-report-popular'],
    ['/admin/reports?tab=activity', '20-admin-report-activity'],
    ['/admin/reports?tab=revenue', '21-admin-report-revenue'],
    ['/admin/settings', '22-admin-settings'],
  ]
  for (const [path, name] of rest) {
    await goto(page, path)
    await settle(page)
    await shot(page, name)
  }
  await page.context().close()
}

// ---------------------------------------------------------------- main

async function main(): Promise<void> {
  await ensureReachable()
  mkdirSync(OUT_DIR, { recursive: true })

  const adminTokens = await login(ADMIN, 'Перевірте ADMIN_EMAIL / ADMIN_PASSWORD у backend/.env і запустіть python -m app.seed.')
  const movie = await findMovieWithVideo(adminTokens.access_token)
  const premium = await findPremiumUser(adminTokens.access_token)
  console.log(`Фільм з відео: «${movie.name}» (id ${movie.id})`)

  const browser = await launchBrowser()
  try {
    await guestScreens(browser)
    await freeUserScreens(browser, movie)
    await premiumUserScreens(browser, premium, movie)
    await paymentScreens(browser)
    await adminScreens(browser, adminTokens, movie)
  } finally {
    await browser.close()
  }
  console.log(`Готово: ${taken} знімків у ${OUT_DIR}`)
}

main().catch((error: unknown) => {
  console.error(`✗ ${error instanceof Error ? error.message : String(error)}`)
  process.exit(1)
})
