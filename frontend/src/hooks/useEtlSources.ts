import { useState, useEffect } from 'react'
import type { EtlSource } from '@/types/etlSource.types'
import { etlSourceService } from '@/services/etlSource.service'

interface UseEtlSourcesReturn {
  etlSources: EtlSource[]
  loading: boolean
  error: Error | null
  refetch: () => Promise<void>
}

export function useEtlSources(): UseEtlSourcesReturn {
  const [etlSources, setEtlSources] = useState<EtlSource[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchEtlSources = async () => {
    setLoading(true)
    setError(null)

    const { data, error: fetchError } = await etlSourceService.getAll()

    if (fetchError) {
      setError(fetchError)
      setEtlSources([])
    } else {
      setEtlSources(data || [])
    }

    setLoading(false)
  }

  useEffect(() => {
    fetchEtlSources()
  }, [])

  return {
    etlSources,
    loading,
    error,
    refetch: fetchEtlSources
  }
}
