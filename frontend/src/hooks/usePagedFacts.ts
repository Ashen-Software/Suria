import { useEffect, useMemo } from 'react'
import { useInfiniteQuery } from '@tanstack/react-query'
import type { GasNaturalRecord, EnergiaElectricaRecord } from '@/types/upme.types'
import type { OfertaGasRecord, RegaliasRecord } from '@/types/declaracion_regalias.types'
import { loadGasNaturalPage, loadEnergiaElectricaPage } from '@/services/upmeData.service'
import { loadOfertaGasPage, loadRegaliasPage } from '@/services/declaracionRegaliasData.service'

const API_PAGE_SIZE = 5000

interface PagedResult<T> {
  flatData: T[]
  isLoading: boolean
  error: unknown
  hasNextPage: boolean | undefined
  isFetchingNextPage: boolean
  allPagesLoaded: boolean
}

function useAutoPaging<T>(
  queryKey: (string | number)[],
  loader: (page: number, pageSize: number) => Promise<T[]>,
): PagedResult<T> {
  const {
    data,
    isLoading,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery<T[]>({
    queryKey,
    queryFn: async ({ pageParam }) => loader((pageParam as number) ?? 0, API_PAGE_SIZE),
    getNextPageParam: (lastPage, allPages) =>
      lastPage.length === API_PAGE_SIZE ? allPages.length : undefined,
    initialPageParam: 0,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  })

  // Cargar páginas adicionales automáticamente para que el dashboard se vaya completando solo
  useEffect(() => {
    if (hasNextPage && !isFetchingNextPage) {
      fetchNextPage()
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage])

  const flatData: T[] = useMemo(
    () => ((data?.pages as T[][]) ?? []).flat(),
    [data],
  )

  const allPagesLoaded = hasNextPage === false

  return {
    flatData,
    isLoading,
    error,
    hasNextPage,
    isFetchingNextPage,
    allPagesLoaded,
  }
}

// Hooks específicos por tabla de hechos

export function useGasNaturalPaged(): PagedResult<GasNaturalRecord> {
  return useAutoPaging<GasNaturalRecord>(['fact-demanda-gas-natural', 'paged'], loadGasNaturalPage)
}

export function useEnergiaElectricaPaged(): PagedResult<EnergiaElectricaRecord> {
  return useAutoPaging<EnergiaElectricaRecord>(
    ['fact-energia-electrica', 'paged'],
    loadEnergiaElectricaPage,
  )
}

export function useOfertaGasPaged(): PagedResult<OfertaGasRecord> {
  return useAutoPaging<OfertaGasRecord>(['fact-oferta-gas', 'paged'], loadOfertaGasPage)
}

export function useRegaliasPaged(): PagedResult<RegaliasRecord> {
  return useAutoPaging<RegaliasRecord>(['fact-regalias', 'paged'], loadRegaliasPage)
}


