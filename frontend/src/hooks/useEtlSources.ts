import { useQuery } from '@tanstack/react-query'
import { etlSourceService } from '@/services/etlSource.service'

export function useEtlSources(params?: { page?: number; pageSize?: number }) {
  return useQuery({
    queryKey: ['etlSources', params?.page, params?.pageSize],
    queryFn: async () => {
      const { data, error, count } = await etlSourceService.getAll(params)
      if (error) throw error
      return { data: data || [], count: count ?? 0 }
    },
  })
}
