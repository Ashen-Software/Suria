/**
 * Tipos para tablas fact_oferta_gas y fact_regalias
 * basados en el esquema de Supabase.
 */

export interface OfertaGasRecord {
  id: number
  period_key: string // YYYY-MM-DD derivado de dim_tiempo.fecha
  tiempo_id: number
  campo_id: number
  resolucion_id: number | null
  tipo_produccion: string | null
  operador: string
  es_operador_campo: boolean | null
  es_participacion_estado: boolean | null
  valor_gbtud: number
  poder_calorifico_btu_pc: number | null
  source_id: string | null
  etl_timestamp: string | null
}

export interface RegaliasRecord {
  id: number
  period_key: string // YYYY-MM-DD derivado de dim_tiempo.fecha
  tiempo_id: number | null
  campo_id: number | null
  tipo_produccion: string | null
  tipo_hidrocarburo: string | null
  precio_usd: number | null
  porcentaje_regalia: number | null
  produccion_gravable: number | null
  volumen_regalia: number | null
  unidad: string | null
  valor_regalias_cop: number | null
  source_id: string | null
  etl_timestamp: string | null
  regimen_regalias: string | null
}


