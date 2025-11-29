import { supabase } from '@/config/supabase'
import type { RegaliasRecord } from '@/types/declaracion_regalias.types'

export class FactRegaliasService {
  private static instance: FactRegaliasService

  private constructor() {}

  static getInstance(): FactRegaliasService {
    if (!FactRegaliasService.instance) {
      FactRegaliasService.instance = new FactRegaliasService()
    }
    return FactRegaliasService.instance
  }

  /**
   * Obtiene los registros de liquidación de regalías por campo
   * con join a dim_tiempo.
   *
   * Para evitar timeouts en Supabase, se limita el número de filas
   * devueltas a un máximo razonable para exploración en el front.
   */
  async getAll(): Promise<{
    data: RegaliasRecord[] | null
    error: Error | null
  }> {
    try {
      const pageSize = 5000
      let from = 0
      let hasMore = true
      const allRecords: RegaliasRecord[] = []

      while (hasMore) {
        const to = from + pageSize - 1

        const { data, error } = await supabase
          .from('fact_regalias')
          .select(
            `
            *,
            dim_tiempo (
              fecha
            )
          `
          )
          .order('tiempo_id', { ascending: true })
          .range(from, to)

        if (error) {
          console.error('Error fetching fact_regalias:', error)
          return { data: null, error: new Error(error.message) }
        }

        const chunk = data || []

        const mappedChunk: RegaliasRecord[] = chunk.map((record: any) => {
          const fecha = record.dim_tiempo?.fecha || null
          const periodKey = fecha ? new Date(fecha).toISOString().split('T')[0] : ''

          return {
            id: record.id,
            period_key: periodKey,
            tiempo_id: record.tiempo_id ?? null,
            campo_id: record.campo_id ?? null,
            tipo_produccion: record.tipo_produccion ?? null,
            tipo_hidrocarburo: record.tipo_hidrocarburo ?? null,
            precio_usd: record.precio_usd != null ? Number(record.precio_usd) : null,
            porcentaje_regalia: record.porcentaje_regalia != null ? Number(record.porcentaje_regalia) : null,
            produccion_gravable: record.produccion_gravable != null ? Number(record.produccion_gravable) : null,
            volumen_regalia: record.volumen_regalia != null ? Number(record.volumen_regalia) : null,
            unidad: record.unidad ?? null,
            valor_regalias_cop: record.valor_regalias_cop != null ? Number(record.valor_regalias_cop) : null,
            source_id: record.source_id ?? null,
            etl_timestamp: record.etl_timestamp ?? null,
            regimen_regalias: record.regimen_regalias ?? null,
          }
        })

        allRecords.push(...mappedChunk)

        if (chunk.length < pageSize) {
          hasMore = false
        } else {
          from += pageSize
        }
      }

      return { data: allRecords, error: null }
    } catch (error) {
      console.error('Unexpected error:', error)
      return {
        data: null,
        error: error instanceof Error ? error : new Error('Unknown error occurred'),
      }
    }
  }

  /**
   * Obtiene una página de registros de regalías,
   * pensada para carga incremental desde el frontend.
   */
  async getPage(from: number, to: number): Promise<{
    data: RegaliasRecord[] | null
    error: Error | null
  }> {
    try {
      const { data, error } = await supabase
        .from('fact_regalias')
        .select(
          `
          *,
          dim_tiempo (
            fecha
          )
        `
        )
        .order('tiempo_id', { ascending: true })
        .range(from, to)

      if (error) {
        console.error('Error fetching fact_regalias page:', error)
        return { data: null, error: new Error(error.message) }
      }

      const mapped: RegaliasRecord[] = (data || []).map((record: any) => {
        const fecha = record.dim_tiempo?.fecha || null
        const periodKey = fecha ? new Date(fecha).toISOString().split('T')[0] : ''

        return {
          id: record.id,
          period_key: periodKey,
          tiempo_id: record.tiempo_id ?? null,
          campo_id: record.campo_id ?? null,
          tipo_produccion: record.tipo_produccion ?? null,
          tipo_hidrocarburo: record.tipo_hidrocarburo ?? null,
          precio_usd: record.precio_usd != null ? Number(record.precio_usd) : null,
          porcentaje_regalia: record.porcentaje_regalia != null ? Number(record.porcentaje_regalia) : null,
          produccion_gravable: record.produccion_gravable != null ? Number(record.produccion_gravable) : null,
          volumen_regalia: record.volumen_regalia != null ? Number(record.volumen_regalia) : null,
          unidad: record.unidad ?? null,
          valor_regalias_cop: record.valor_regalias_cop != null ? Number(record.valor_regalias_cop) : null,
          source_id: record.source_id ?? null,
          etl_timestamp: record.etl_timestamp ?? null,
          regimen_regalias: record.regimen_regalias ?? null,
        }
      })

      return { data: mapped, error: null }
    } catch (error) {
      console.error('Unexpected error (page):', error)
      return {
        data: null,
        error: error instanceof Error ? error : new Error('Unknown error occurred'),
      }
    }
  }
}

export const factRegaliasService = FactRegaliasService.getInstance()


