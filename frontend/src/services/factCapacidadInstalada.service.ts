import { supabase } from '@/config/supabase'
import type { CapacidadInstaladaRecord } from '@/types/upme.types'

export class FactCapacidadInstaladaService {
  private static instance: FactCapacidadInstaladaService

  private constructor() {}

  static getInstance(): FactCapacidadInstaladaService {
    if (!FactCapacidadInstaladaService.instance) {
      FactCapacidadInstaladaService.instance = new FactCapacidadInstaladaService()
    }
    return FactCapacidadInstaladaService.instance
  }

  /**
   * Obtiene los registros de capacidad instalada con join a dim_tiempo
   *
   * OPTIMIZACIÓN:
   * - Esta tabla ya está agregada a nivel anual y su tamaño es
   *   mucho menor, por lo que no se aplican más filtros aquí.
   */
  async getAll(): Promise<{ 
    data: CapacidadInstaladaRecord[] | null; 
    error: Error | null;
  }> {
    try {
      const { data, error } = await supabase
        .from('fact_capacidad_instalada')
        .select(`
          *,
          dim_tiempo (
            fecha
          )
        `)
        .order('tiempo_id', { ascending: true })

      if (error) {
        console.error('Error fetching fact_capacidad_instalada:', error)
        return { data: null, error: new Error(error.message) }
      }

      // Mapear los datos de Supabase al formato esperado por los componentes
      const mappedData: CapacidadInstaladaRecord[] = (data || []).map((record: any) => {
        const fecha = record.dim_tiempo?.fecha || null
        const periodKey = fecha ? new Date(fecha).toISOString().split('T')[0] : ''
        
        return {
          period_key: periodKey,
          periodicidad: record.periodicidad as 'mensual' | 'anual',
          metric: 'capacidad' as const,
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
   * Obtiene una página de registros de capacidad instalada,
   * pensada para carga incremental desde el frontend.
   */
  async getPage(from: number, to: number): Promise<{
    data: CapacidadInstaladaRecord[] | null;
    error: Error | null;
  }> {
    try {
      const { data, error } = await supabase
        .from('fact_capacidad_instalada')
        .select(`
          *,
          dim_tiempo (
            fecha
          )
        `)
        .order('tiempo_id', { ascending: true })
        .range(from, to)

      if (error) {
        console.error('Error fetching fact_capacidad_instalada page:', error)
        return { data: null, error: new Error(error.message) }
      }

      const mappedData: CapacidadInstaladaRecord[] = (data || []).map((record: any) => {
        const fecha = record.dim_tiempo?.fecha || null
        const periodKey = fecha ? new Date(fecha).toISOString().split('T')[0] : ''
        
        return {
          period_key: periodKey,
          periodicidad: record.periodicidad as 'mensual' | 'anual',
          metric: 'capacidad' as const,
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

export const factCapacidadInstaladaService = FactCapacidadInstaladaService.getInstance()

