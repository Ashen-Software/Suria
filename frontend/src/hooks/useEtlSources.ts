import { useQuery } from '@tanstack/react-query'
import { etlSourceService } from '@/services/etlSource.service'

export function useEtlSources() {
  return useQuery({
    queryKey: ['etlSources'],
    queryFn: async () => {
      const { data, error } = await etlSourceService.getAll()
      if (error) throw error
      return data || []
    },
  })
}
