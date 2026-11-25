import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { adminReportKeys } from '../api/adminReports'
import { adminSettingsApi, adminSettingsKeys } from '../api/adminSettings'
import { recommendationKeys } from '../api/recommendations'
import type { AppSettingsPayload } from '../types/settings'

export function useAppSettings() {
  return useQuery({ queryKey: adminSettingsKeys.all, queryFn: adminSettingsApi.get })
}

export function useSaveSettings() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: (payload: AppSettingsPayload) => adminSettingsApi.update(payload),
    onSuccess: (saved) => {
      client.setQueryData(adminSettingsKeys.all, saved)
      void client.invalidateQueries({ queryKey: recommendationKeys.all })
      void client.invalidateQueries({ queryKey: adminReportKeys.all })
    },
  })
}
