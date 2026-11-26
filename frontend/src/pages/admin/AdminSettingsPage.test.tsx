import { fireEvent, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { callsTo, errorResponse, mockApi, renderApp, signedInAs, testAdmin, type RouteHandler } from '../../test/utils'
import type { AppSettings, AppSettingsPayload } from '../../types/settings'

const settings: AppSettings = {
  recommendation_default_strategy: 'hybrid',
  hybrid_weights: { genre_affinity: 0.5, similar: 0.3, popularity: 0.2 },
  popularity_window_days: 7,
  report_timezone: 'Europe/Kyiv',
  available_strategies: ['popularity', 'genre_affinity', 'similar', 'hybrid'],
  updated_at: null,
}

async function openSettings(save: RouteHandler = (_url, init) => Response.json({ ...settings, ...JSON.parse(String(init?.body)) })) {
  const fetchMock = mockApi({ ...signedInAs(testAdmin), 'GET /api/admin/settings': settings, 'PUT /api/admin/settings': save })
  renderApp('/admin/settings')
  await screen.findByRole('heading', { name: 'Налаштування' })
  await screen.findByLabelText('Стратегія рекомендацій за замовчуванням')
  return fetchMock
}

function submit() {
  fireEvent.click(screen.getByRole('button', { name: 'Зберегти' }))
}

describe('AdminSettingsPage', () => {
  it('shows current values with a slider per hybrid component', async () => {
    await openSettings()

    expect(screen.getByLabelText('Стратегія рекомендацій за замовчуванням')).toHaveValue('hybrid')
    expect(screen.getByRole('option', { name: 'За улюбленими жанрами' })).toBeInTheDocument()
    expect(screen.getByLabelText('Вікно популярності, днів')).toHaveValue(7)
    expect(screen.getByRole('slider', { name: 'За улюбленими жанрами' })).toHaveValue('0.5')
    expect(screen.getByRole('slider', { name: 'Популярне' })).toHaveValue('0.2')
    expect(screen.queryByRole('slider', { name: 'Гібридна' })).not.toBeInTheDocument()
    expect(screen.getByText('Діють значення за замовчуванням')).toBeInTheDocument()
  })

  it('validates the form before sending it', async () => {
    const fetchMock = await openSettings()

    for (const name of ['За улюбленими жанрами', 'Схоже на переглянуте', 'Популярне']) {
      fireEvent.change(screen.getByRole('slider', { name }), { target: { value: '0' } })
    }
    fireEvent.change(screen.getByLabelText('Вікно популярності, днів'), { target: { value: '400' } })
    submit()

    expect(screen.getByText('Хоча б одна вага має бути більшою за 0')).toBeInTheDocument()
    expect(screen.getByText('Ціле число від 1 до 365')).toBeInTheDocument()
    expect(callsTo(fetchMock, 'PUT', '/api/admin/settings')).toHaveLength(0)
  })

  it('saves the full settings and reports success', async () => {
    const fetchMock = await openSettings()

    fireEvent.change(screen.getByLabelText('Стратегія рекомендацій за замовчуванням'), { target: { value: 'genre_affinity' } })
    fireEvent.change(screen.getByRole('slider', { name: 'Схоже на переглянуте' }), { target: { value: '0' } })
    fireEvent.change(screen.getByLabelText('Вікно популярності, днів'), { target: { value: '30' } })
    submit()

    expect(await screen.findByText(/Налаштування збережено/)).toBeInTheDocument()
    const [call] = callsTo(fetchMock, 'PUT', '/api/admin/settings')
    const payload: AppSettingsPayload = JSON.parse(String(call.init?.body))
    expect(payload).toEqual({
      recommendation_default_strategy: 'genre_affinity',
      hybrid_weights: { popularity: 0.2, genre_affinity: 0.5, similar: 0 },
      popularity_window_days: 30,
      report_timezone: 'Europe/Kyiv',
    })
  })

  it('shows server errors next to the fields', async () => {
    const responses = [
      errorResponse(422, 'unknown_timezone'),
      errorResponse(422, 'validation_error', [{ loc: ['body', 'popularity_window_days'], msg: 'Забагато днів', type: 'x' }]),
      errorResponse(422, 'unknown_strategy'),
    ]
    await openSettings(() => responses.shift() ?? errorResponse(500, 'internal_error'))

    submit()
    expect(await screen.findByText('Такого часового поясу немає в базі даних')).toBeInTheDocument()
    expect(screen.getByLabelText('Часовий пояс звітів')).toHaveAttribute('aria-invalid', 'true')

    submit()
    expect(await screen.findByText('Забагато днів')).toBeInTheDocument()

    submit()
    expect(await screen.findByRole('alert')).toHaveTextContent('Невідома стратегія рекомендацій')
  })
})
