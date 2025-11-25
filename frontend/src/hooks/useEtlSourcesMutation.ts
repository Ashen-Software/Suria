import { useMutation, useQueryClient } from '@tanstack/react-query'
import { etlSourceService } from '@/services/etlSource.service'
import type { EtlSource, EtlSourceFormData } from '@/types/etlSource.types'

export function useCreateEtlSource() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: EtlSourceFormData) => etlSourceService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['etlSources'] })
    },
  })
}

export function useUpdateEtlSource() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<EtlSource> }) =>
      etlSourceService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['etlSources'] })
    },
  })
}

export function useDeleteEtlSource() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => etlSourceService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['etlSources'] })
    },
  })
}
