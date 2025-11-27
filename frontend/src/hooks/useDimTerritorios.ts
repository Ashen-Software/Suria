import { useQuery } from '@tanstack/react-query'
import { dimTerritoriosService } from '@/services/dimTerritorios.service'

export function useDimTerritorios(params?: { page?: number; pageSize?: number }) {
  return useQuery({
    queryKey: ['dimTerritorios', params?.page, params?.pageSize],
    queryFn: async () => {
      const { data, error, count } = await dimTerritoriosService.getAll(params)
      if (error) throw error
      return { data: data || [], count: count ?? 0 }
    },
  })
}
