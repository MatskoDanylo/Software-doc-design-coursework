import type { HistoryEntry } from '../types/history'
import { apiRequest } from './client'

export const CONTINUE_WATCHING_LIMIT = 12

export const historyApi = {
  continueWatching: () => apiRequest<HistoryEntry[]>(`/api/history?limit=${CONTINUE_WATCHING_LIMIT}`),
}

export const historyKeys = {
  all: ['history'] as const,
}
