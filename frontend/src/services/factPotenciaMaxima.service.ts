import { supabase } from '@/config/supabase'
import type { PotenciaMaximaRecord } from '@/types/upme.types'

export class FactPotenciaMaximaService {
  private static instance: FactPotenciaMaximaService

  private constructor() {}

  static getInstance(): FactPotenciaMaximaService {
    if (!FactPotenciaMaximaService.instance) {
      FactPotenciaMaximaService.instance = new FactPotenciaMaximaService()
    }
    return FactPotenciaMaximaService.instance
  }

  /**
   * Obtiene los registros de potencia máxima con join a dim_tiempo
   *
   * OPTIMIZACIÓN:
   * - Solo trae registros con periodicidad = 'mensual', que son
   *   los usados por los componentes (se agregan por año en el front).
   */
  async getAll(): Promise<{ 
    data: PotenciaMaximaRecord[] | null; 
    error: Error | null;
  }> {
    try {
      const { data, error } = await supabase
        .from('fact_potencia_maxima')
        .select(`
          *,
          dim_tiempo (
            fecha
          )
        `)
        .eq('periodicidad', 'mensual')
        .order('tiempo_id', { ascending: true })

      if (error) {
        console.error('Error fetching fact_potencia_maxima:', error)
        return { data: null, error: new Error(error.message) }
      }

      // Mapear los datos de Supabase al formato esperado por los componentes
      const mappedData: PotenciaMaximaRecord[] = (data || []).map((record: any) => {
        const fecha = record.dim_tiempo?.fecha || null
        const periodKey = fecha ? new Date(fecha).toISOString().split('T')[0] : ''
        
        return {
          period_key: periodKey,
          periodicidad: record.periodicidad as 'mensual' | 'anual',
          metric: 'potencia' as const,
          unidad: record.unidad || '',
          ambito: record.ambito || '',
          descriptor: record.descriptor || '',
          escenario: record.escenario as 'ESC_BAJO' | 'ESC_MEDIO' | 'ESC_ALTO',
          valor: parseFloat(record.valor) || 0,
          revision: record.revision || '',
          year_span: record.year_span || '',
          sheet_name: record.sheet_name || '',
          source_file: record.source_file || '',
        }
      })

      return { data: mappedData, error: null }
    } catch (error) {
      console.error('Unexpected error:', error)
      return { 
        data: null, 
        error: error instanceof Error ? error : new Error('Unknown error occurred')
      }
    }
  }

  /**
   * Obtiene una página de registros de potencia máxima,
   * pensada para carga incremental desde el frontend.
   */
  async getPage(from: number, to: number): Promise<{
    data: PotenciaMaximaRecord[] | null
    error: Error | null
  }> {
    try {
      const { data, error } = await supabase
        .from('fact_potencia_maxima')
        .select(`
          *,
          dim_tiempo (
            fecha
          )
        `)
        .eq('periodicidad', 'mensual')
        .order('tiempo_id', { ascending: true })
        .range(from, to)

      if (error) {
        console.error('Error fetching fact_potencia_maxima page:', error)
        return { data: null, error: new Error(error.message) }
      }

      const mappedData: PotenciaMaximaRecord[] = (data || []).map((record: any) => {
        const fecha = record.dim_tiempo?.fecha || null
        const periodKey = fecha ? new Date(fecha).toISOString().split('T')[0] : ''
        
        return {
          period_key: periodKey,
          periodicidad: record.periodicidad as 'mensual' | 'anual',
          metric: 'potencia' as const,
          unidad: record.unidad || '',
          ambito: record.ambito || '',
          descriptor: record.descriptor || '',
          escenario: record.escenario as 'ESC_BAJO' | 'ESC_MEDIO' | 'ESC_ALTO',
          valor: parseFloat(record.valor) || 0,
          revision: record.revision || '',
          year_span: record.year_span || '',
          sheet_name: record.sheet_name || '',
          source_file: record.source_file || '',
        }
      })

      return { data: mappedData, error: null }
    } catch (error) {
      console.error('Unexpected error (page):', error)
      return { 
        data: null, 
        error: error instanceof Error ? error : new Error('Unknown error occurred')
      }
    }
  }
}

export const factPotenciaMaximaService = FactPotenciaMaximaService.getInstance()

