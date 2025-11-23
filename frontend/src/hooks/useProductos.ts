import { useState, useEffect } from 'react'
import type { Producto } from '@/types/producto.types'
import { productoService } from '@/services/producto.service'

interface UseProductosReturn {
  productos: Producto[]
  loading: boolean
  error: Error | null
  refetch: () => Promise<void>
}

export function useProductos(): UseProductosReturn {
  const [productos, setProductos] = useState<Producto[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchProductos = async () => {
    setLoading(true)
    setError(null)

    const { data, error: fetchError } = await productoService.getAll()

    if (fetchError) {
      setError(fetchError)
      setProductos([])
    } else {
      setProductos(data || [])
    }

    setLoading(false)
  }

  useEffect(() => {
    fetchProductos()
  }, [])

  return {
    productos,
    loading,
    error,
    refetch: fetchProductos
  }
}
