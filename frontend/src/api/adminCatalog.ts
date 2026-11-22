import type { EpisodePayload, GenrePayload, SeasonPayload, TitlePayload } from '../types/adminCatalog'
import type { Episode, Genre, Season, Title, TitleDetail } from '../types/catalog'
import { apiRequest } from './client'

function posterForm(file: File): FormData {
  const form = new FormData()
  form.append('file', file)
  return form
}

export const adminCatalogApi = {
  createTitle: (data: TitlePayload) => apiRequest<TitleDetail>('/api/admin/titles', { method: 'POST', body: data }),
  updateTitle: (id: number, data: Partial<TitlePayload>) =>
    apiRequest<TitleDetail>(`/api/admin/titles/${id}`, { method: 'PATCH', body: data }),
  deleteTitle: (id: number) => apiRequest<null>(`/api/admin/titles/${id}`, { method: 'DELETE' }),
  uploadPoster: (id: number, file: File) =>
    apiRequest<Title>(`/api/admin/titles/${id}/poster`, { method: 'POST', body: posterForm(file) }),

  createGenre: (data: GenrePayload) => apiRequest<Genre>('/api/admin/genres', { method: 'POST', body: data }),
  updateGenre: (id: number, data: GenrePayload) =>
    apiRequest<Genre>(`/api/admin/genres/${id}`, { method: 'PATCH', body: data }),
  deleteGenre: (id: number) => apiRequest<null>(`/api/admin/genres/${id}`, { method: 'DELETE' }),

  createSeason: (titleId: number, data: SeasonPayload) =>
    apiRequest<Season>(`/api/admin/titles/${titleId}/seasons`, { method: 'POST', body: data }),
  updateSeason: (id: number, data: SeasonPayload) =>
    apiRequest<Season>(`/api/admin/seasons/${id}`, { method: 'PATCH', body: data }),
  deleteSeason: (id: number) => apiRequest<null>(`/api/admin/seasons/${id}`, { method: 'DELETE' }),

  createEpisode: (seasonId: number, data: EpisodePayload) =>
    apiRequest<Episode>(`/api/admin/seasons/${seasonId}/episodes`, { method: 'POST', body: data }),
  updateEpisode: (id: number, data: Partial<EpisodePayload>) =>
    apiRequest<Episode>(`/api/admin/episodes/${id}`, { method: 'PATCH', body: data }),
  deleteEpisode: (id: number) => apiRequest<null>(`/api/admin/episodes/${id}`, { method: 'DELETE' }),
}
