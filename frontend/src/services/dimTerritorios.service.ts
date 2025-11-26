import { supabase } from '@/config/supabase'
import type { DimTerritorios } from '@/types/dim_territorios.types'

export class DimTerritoriosService {
  private static instance: DimTerritoriosService

  private constructor() {}

  static getInstance(): DimTerritoriosService {
    if (!DimTerritoriosService.instance) {
      DimTerritoriosService.instance = new DimTerritoriosService()
    }
    return DimTerritoriosService.instance
  }

  async getAll(params?: { 
    page?: number; 
    pageSize?: number 
  }): Promise<{ 
    data: DimTerritorios[] | null; 
    error: Error | null;
    count: number | null;
  }> {
    try {
      const page = params?.page ?? 0
      const pageSize = params?.pageSize ?? 10
      const from = page * pageSize
      const to = from + pageSize - 1

      const { data, error, count } = await supabase
        .from('dim_territorios')
        .select('*', { count: 'exact' })
        .order('departamento', { ascending: true })
        .order('municipio', { ascending: true })
        .range(from, to)

      if (error) {
        console.error('Error fetching dim_territorios:', error)
        return { data: null, error: new Error(error.message), count: null }
      }

      return { data: data as DimTerritorios[], error: null, count: count ?? 0 }
    } catch (error) {
      console.error('Unexpected error:', error)
      return { 
        data: null, 
        error: error instanceof Error ? error : new Error('Unknown error occurred'),
        count: null
      }
    }
  }

  async getById(id: number): Promise<{ data: DimTerritorios | null; error: Error | null }> {
    try {
      const { data, error } = await supabase
        .from('dim_territorios')
        .select('*')
        .eq('id', id)
        .single()

      if (error) {
        console.error('Error fetching dim_territorios:', error)
        return { data: null, error: new Error(error.message) }
      }

      return { data: data as DimTerritorios, error: null }
    } catch (error) {
      console.error('Unexpected error:', error)
      return { 
        data: null, 
        error: error instanceof Error ? error : new Error('Unknown error occurred') 
      }
    }
  }

  async getByDepartamento(departamento: string): Promise<{ data: DimTerritorios[] | null; error: Error | null }> {
    try {
      const { data, error } = await supabase
        .from('dim_territorios')
        .select('*')
        .eq('departamento', departamento)
        .order('municipio', { ascending: true })

      if (error) {
        console.error('Error fetching dim_territorios by departamento:', error)
        return { data: null, error: new Error(error.message) }
      }

      return { data: data as DimTerritorios[], error: null }
    } catch (error) {
      console.error('Unexpected error:', error)
      return { 
        data: null, 
        error: error instanceof Error ? error : new Error('Unknown error occurred') 
      }
    }
  }
}

export const dimTerritoriosService = DimTerritoriosService.getInstance()
