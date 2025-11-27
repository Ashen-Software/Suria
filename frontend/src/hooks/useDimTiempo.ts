import { useQuery } from '@tanstack/react-query'
import { dimTiempoService } from '@/services/dimTiempo.service'

export function useDimTiempo(params?: { page?: number; pageSize?: number }) {
  return useQuery({
    queryKey: ['dimTiempo', params?.page, params?.pageSize],
    queryFn: async () => {
      const { data, error, count } = await dimTiempoService.getAll(params)
      if (error) throw error
      return { data: data || [], count: count ?? 0 }
    },
  })
}
