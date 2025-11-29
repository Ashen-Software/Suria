import { supabase } from '@/config/supabase'
import type { GasNaturalRecord } from '@/types/upme.types'

export class FactDemandaGasNaturalService {
  private static instance: FactDemandaGasNaturalService

  private constructor() {}

  static getInstance(): FactDemandaGasNaturalService {
    if (!FactDemandaGasNaturalService.instance) {
      FactDemandaGasNaturalService.instance = new FactDemandaGasNaturalService()
    }
    return FactDemandaGasNaturalService.instance
  }

  /**
   * Obtiene los registros de demanda de gas natural con join a dim_tiempo
   *
   * OPTIMIZACIÓN:
   * - Solo trae registros con:
   *   - periodicidad = 'mensual'
   *   - escenario en ('ESC_BAJO', 'ESC_MEDIO', 'ESC_ALTO')
   *   que son los únicos usados por los gráficos.
   */
  async getAll(): Promise<{ 
    data: GasNaturalRecord[] | null; 
    error: Error | null;
  }> {
    try {
      const { data, error } = await supabase
        .from('fact_demanda_gas_natural')
        .select(`
          *,
          dim_tiempo (
            fecha
          )
        `)
        .eq('periodicidad', 'mensual')
        .in('escenario', ['ESC_BAJO', 'ESC_MEDIO', 'ESC_ALTO'])
        .order('tiempo_id', { ascending: true })

      if (error) {
        console.error('Error fetching fact_demanda_gas_natural:', error)
        return { data: null, error: new Error(error.message) }
      }

      // Mapear los datos de Supabase al formato esperado por los componentes
      const mappedData: GasNaturalRecord[] = (data || []).map((record: any) => {
        const fecha = record.dim_tiempo?.fecha || null
        const periodKey = fecha ? new Date(fecha).toISOString().split('T')[0] : ''
        
        return {
          period_key: periodKey,
          periodicidad: record.periodicidad as 'mensual' | 'anual',
          categoria: record.categoria as GasNaturalRecord['categoria'],
          region: record.region || null,
          nodo: record.nodo || null,
          escenario: record.escenario as 'ESC_BAJO' | 'ESC_MEDIO' | 'ESC_ALTO',
          valor: parseFloat(record.valor) || 0,
          unidad: record.unidad || 'GBTUD',
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
   * Obtiene una página de registros de demanda de gas natural,
   * pensada para carga incremental desde el frontend.
   */
  async getPage(from: number, to: number): Promise<{
    data: GasNaturalRecord[] | null;
    error: Error | null;
  }> {
    try {
      const { data, error } = await supabase
        .from('fact_demanda_gas_natural')
        .select(`
          *,
          dim_tiempo (
            fecha
          )
        `)
        .eq('periodicidad', 'mensual')
        .in('escenario', ['ESC_BAJO', 'ESC_MEDIO', 'ESC_ALTO'])
        .order('tiempo_id', { ascending: true })
        .range(from, to)

      if (error) {
        console.error('Error fetching fact_demanda_gas_natural page:', error)
        return { data: null, error: new Error(error.message) }
      }

      const mappedData: GasNaturalRecord[] = (data || []).map((record: any) => {
        const fecha = record.dim_tiempo?.fecha || null
        const periodKey = fecha ? new Date(fecha).toISOString().split('T')[0] : ''
        
        return {
          period_key: periodKey,
          periodicidad: record.periodicidad as 'mensual' | 'anual',
          categoria: record.categoria as GasNaturalRecord['categoria'],
          region: record.region || null,
          nodo: record.nodo || null,
          escenario: record.escenario as 'ESC_BAJO' | 'ESC_MEDIO' | 'ESC_ALTO',
          valor: parseFloat(record.valor) || 0,
          unidad: record.unidad || 'GBTUD',
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

export const factDemandaGasNaturalService = FactDemandaGasNaturalService.getInstance()

