import { supabase } from '@/config/supabase'
import type { EnergiaElectricaRecord } from '@/types/upme.types'

export class FactEnergiaElectricaService {
  private static instance: FactEnergiaElectricaService

  private constructor() {}

  static getInstance(): FactEnergiaElectricaService {
    if (!FactEnergiaElectricaService.instance) {
      FactEnergiaElectricaService.instance = new FactEnergiaElectricaService()
    }
    return FactEnergiaElectricaService.instance
  }

  /**
   * Obtiene los registros de energía eléctrica con join a dim_tiempo
   *
   * OPTIMIZACIÓN:
   * - Solo trae:
   *   - Todos los registros de periodicidad = 'anual' (todos los escenarios)
   *   - Registros de periodicidad = 'mensual' para escenario = 'ESC_MEDIO'
   *   que son los únicos usados en los charts.
   */
  async getAll(): Promise<{ 
    data: EnergiaElectricaRecord[] | null; 
    error: Error | null;
  }> {
    try {
      const { data, error } = await supabase
        .from('fact_energia_electrica')
        .select(`
          *,
          dim_tiempo (
            fecha
          )
        `)
        // Traer solo lo necesario para los gráficos
        .or('periodicidad.eq.anual,and(periodicidad.eq.mensual,escenario.eq.ESC_MEDIO)')
        .order('tiempo_id', { ascending: true })

      if (error) {
        console.error('Error fetching fact_energia_electrica:', error)
        return { data: null, error: new Error(error.message) }
      }

      // Mapear los datos de Supabase al formato esperado por los componentes
      const mappedData: EnergiaElectricaRecord[] = (data || []).map((record: any) => {
        const fecha = record.dim_tiempo?.fecha || null
        const periodKey = fecha ? new Date(fecha).toISOString().split('T')[0] : ''
        
        return {
          period_key: periodKey,
          periodicidad: record.periodicidad as 'mensual' | 'anual',
          metric: 'energia' as const,
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
}

export const factEnergiaElectricaService = FactEnergiaElectricaService.getInstance()

