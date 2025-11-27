/**
 * Tabla: public.dim_territorios
 * 
 * Constraints:
 * - PRIMARY KEY: dim_territorios_pkey (id)
 * - UNIQUE: dim_territorios_departamento_municipio_key (departamento, municipio)
 * 
 * Descripción:
 * Dimensión de territorios que almacena información geográfica de departamentos y municipios
 * con sus coordenadas y código DIVIPOLA.
 */
export interface DimTerritorios {
  id: number
  departamento: string
  municipio: string
  latitud: number | null
  longitud: number | null
  divipola: string | null
  created_at: string | null // DEFAULT: now()
}

/**
 * Tipo para crear un nuevo territorio (sin id y created_at)
 */
export type DimTerritoriosCreate = Omit<DimTerritorios, 'id' | 'created_at'>

/**
 * Tipo para actualizar un territorio (todos los campos opcionales excepto id)
 */
export type DimTerritoriosUpdate = Partial<Omit<DimTerritorios, 'id' | 'created_at'>>
