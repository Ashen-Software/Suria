/** Meses del año (1-12) */
export const Mes = {
  ENERO: 1,
  FEBRERO: 2,
  MARZO: 3,
  ABRIL: 4,
  MAYO: 5,
  JUNIO: 6,
  JULIO: 7,
  AGOSTO: 8,
  SEPTIEMBRE: 9,
  OCTUBRE: 10,
  NOVIEMBRE: 11,
  DICIEMBRE: 12,
} as const

export type Mes = (typeof Mes)[keyof typeof Mes]

/** Nombres de los meses en español */
export const NOMBRE_MES: Record<Mes, string> = {
  [Mes.ENERO]: 'Enero',
  [Mes.FEBRERO]: 'Febrero',
  [Mes.MARZO]: 'Marzo',
  [Mes.ABRIL]: 'Abril',
  [Mes.MAYO]: 'Mayo',
  [Mes.JUNIO]: 'Junio',
  [Mes.JULIO]: 'Julio',
  [Mes.AGOSTO]: 'Agosto',
  [Mes.SEPTIEMBRE]: 'Septiembre',
  [Mes.OCTUBRE]: 'Octubre',
  [Mes.NOVIEMBRE]: 'Noviembre',
  [Mes.DICIEMBRE]: 'Diciembre',
}

/** Trimestres del año (1-4) */
export const Trimestre = {
  Q1: 1,
  Q2: 2,
  Q3: 3,
  Q4: 4,
} as const

export type Trimestre = (typeof Trimestre)[keyof typeof Trimestre]

/** Semestres del año (1-2) */
export const Semestre = {
  S1: 1,
  S2: 2,
} as const

export type Semestre = (typeof Semestre)[keyof typeof Semestre]

/**
 * Tabla: public.dim_tiempo
 * 
 * Constraints:
 * - PRIMARY KEY: dim_tiempo_pkey (id)
 * - UNIQUE: dim_tiempo_fecha_key (fecha)
 * - CHECK: dim_tiempo_mes_check (mes >= 1 AND mes <= 12)
 * 
 * Índices:
 * - idx_tiempo_anio_mes: btree (anio, mes)
 * 
 * Campos generados:
 * - trimestre: GENERATED ALWAYS AS (((mes - 1) / 3) + 1) STORED
 * - semestre: GENERATED ALWAYS AS (CASE WHEN mes <= 6 THEN 1 ELSE 2 END) STORED
 */
export interface DimTiempo {
  id: number
  fecha: string // UNIQUE
  anio: number
  mes: Mes // CHECK: 1-12
  trimestre: Trimestre | null // GENERATED
  semestre: Semestre | null // GENERATED
  nombre_mes: string
  es_proyeccion: boolean | null // DEFAULT: false
  created_at: string | null // DEFAULT: now()
}
