import { supabase } from '@/config/supabase'
import type { OfertaGasRecord } from '@/types/declaracion_regalias.types'

export class FactOfertaGasService {
  private static instance: FactOfertaGasService

  private constructor() {}

  static getInstance(): FactOfertaGasService {
    if (!FactOfertaGasService.instance) {
      FactOfertaGasService.instance = new FactOfertaGasService()
    }
    return FactOfertaGasService.instance
  }

  /**
   * Obtiene los registros de declaración de producción de gas natural
   * con join a dim_tiempo.
   *
   * Para evitar timeouts en Supabase, se limita el número de filas
   * devueltas a un máximo razonable para exploración en el front.
   */
  async getAll(): Promise<{
    data: OfertaGasRecord[] | null
    error: Error | null
  }> {
    try {
      const pageSize = 5000
      let from = 0
      let hasMore = true
      const allRecords: OfertaGasRecord[] = []

      while (hasMore) {
        const to = from + pageSize - 1

        const { data, error } = await supabase
          .from('fact_oferta_gas')
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
          console.error('Error fetching fact_oferta_gas:', error)
          return { data: null, error: new Error(error.message) }
        }

        const chunk = data || []

        const mappedChunk: OfertaGasRecord[] = chunk.map((record: any) => {
          const fecha = record.dim_tiempo?.fecha || null
          const periodKey = fecha ? new Date(fecha).toISOString().split('T')[0] : ''

          return {
            id: record.id,
            period_key: periodKey,
            tiempo_id: record.tiempo_id,
            campo_id: record.campo_id,
            resolucion_id: record.resolucion_id ?? null,
            tipo_produccion: record.tipo_produccion ?? null,
            operador: record.operador ?? '',
            es_operador_campo: typeof record.es_operador_campo === 'boolean' ? record.es_operador_campo : null,
            es_participacion_estado:
              typeof record.es_participacion_estado === 'boolean' ? record.es_participacion_estado : null,
            valor_gbtud: record.valor_gbtud != null ? Number(record.valor_gbtud) : 0,
            poder_calorifico_btu_pc:
              record.poder_calorifico_btu_pc != null ? Number(record.poder_calorifico_btu_pc) : null,
            source_id: record.source_id ?? null,
            etl_timestamp: record.etl_timestamp ?? null,
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
   * Obtiene una página de registros de declaración de gas natural,
   * pensada para estrategias de carga incremental desde el frontend.
   */
  async getPage(from: number, to: number): Promise<{
    data: OfertaGasRecord[] | null
    error: Error | null
  }> {
    try {
      const { data, error } = await supabase
        .from('fact_oferta_gas')
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
        console.error('Error fetching fact_oferta_gas page:', error)
        return { data: null, error: new Error(error.message) }
      }

      const mapped: OfertaGasRecord[] = (data || []).map((record: any) => {
        const fecha = record.dim_tiempo?.fecha || null
        const periodKey = fecha ? new Date(fecha).toISOString().split('T')[0] : ''

        return {
          id: record.id,
          period_key: periodKey,
          tiempo_id: record.tiempo_id,
          campo_id: record.campo_id,
          resolucion_id: record.resolucion_id ?? null,
          tipo_produccion: record.tipo_produccion ?? null,
          operador: record.operador ?? '',
          es_operador_campo: typeof record.es_operador_campo === 'boolean' ? record.es_operador_campo : null,
          es_participacion_estado:
            typeof record.es_participacion_estado === 'boolean' ? record.es_participacion_estado : null,
          valor_gbtud: record.valor_gbtud != null ? Number(record.valor_gbtud) : 0,
          poder_calorifico_btu_pc:
            record.poder_calorifico_btu_pc != null ? Number(record.poder_calorifico_btu_pc) : null,
          source_id: record.source_id ?? null,
          etl_timestamp: record.etl_timestamp ?? null,
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

export const factOfertaGasService = FactOfertaGasService.getInstance()


