import type { OfertaGasRecord, RegaliasRecord } from '@/types/declaracion_regalias.types'
import { factOfertaGasService } from './factOfertaGas.service'
import { factRegaliasService } from './factRegalias.service'

// Versión completa (usa el método getAll con paginación interna)
export async function loadOfertaGasData(): Promise<OfertaGasRecord[]> {
  const { data, error } = await factOfertaGasService.getAll()

  if (error) {
    console.error('Error loading oferta gas data:', error)
    throw error
  }

  return data || []
}

export async function loadRegaliasData(): Promise<RegaliasRecord[]> {
  const { data, error } = await factRegaliasService.getAll()

  if (error) {
    console.error('Error loading regalias data:', error)
    throw error
  }

  return data || []
}

// Versión paginada para carga incremental desde el frontend
export async function loadOfertaGasPage(page: number, pageSize: number): Promise<OfertaGasRecord[]> {
  const from = page * pageSize
  const to = from + pageSize - 1

  const { data, error } = await factOfertaGasService.getPage(from, to)

  if (error) {
    console.error('Error loading oferta gas page:', error)
    throw error
  }

  return data || []
}

export async function loadRegaliasPage(page: number, pageSize: number): Promise<RegaliasRecord[]> {
  const from = page * pageSize
  const to = from + pageSize - 1

  const { data, error } = await factRegaliasService.getPage(from, to)

  if (error) {
    console.error('Error loading regalias page:', error)
    throw error
  }

  return data || []
}

