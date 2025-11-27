import { supabase } from '@/config/supabase'
import type { DimTiempo } from '@/types/dim_tiempo.types'

export class DimTiempoService {
  private static instance: DimTiempoService

  private constructor() {}

  static getInstance(): DimTiempoService {
    if (!DimTiempoService.instance) {
      DimTiempoService.instance = new DimTiempoService()
    }
    return DimTiempoService.instance
  }

  async getAll(params?: { 
    page?: number; 
    pageSize?: number 
  }): Promise<{ 
    data: DimTiempo[] | null; 
    error: Error | null;
    count: number | null;
  }> {
    try {
      const page = params?.page ?? 0
      const pageSize = params?.pageSize ?? 10
      const from = page * pageSize
      const to = from + pageSize - 1

      const { data, error, count } = await supabase
        .from('dim_tiempo')
        .select('*', { count: 'exact' })
        .order('fecha', { ascending: false })
        .range(from, to)

      if (error) {
        console.error('Error fetching dim_tiempo:', error)
        return { data: null, error: new Error(error.message), count: null }
      }

      return { data: data as DimTiempo[], error: null, count: count ?? 0 }
    } catch (error) {
      console.error('Unexpected error:', error)
      return { 
        data: null, 
        error: error instanceof Error ? error : new Error('Unknown error occurred'),
        count: null
      }
    }
  }

  async getById(id: number): Promise<{ data: DimTiempo | null; error: Error | null }> {
    try {
      const { data, error } = await supabase
        .from('dim_tiempo')
        .select('*')
        .eq('id', id)
        .single()

      if (error) {
        console.error('Error fetching dim_tiempo:', error)
        return { data: null, error: new Error(error.message) }
      }

      return { data: data as DimTiempo, error: null }
    } catch (error) {
      console.error('Unexpected error:', error)
      return { 
        data: null, 
        error: error instanceof Error ? error : new Error('Unknown error occurred') 
      }
    }
  }

  async getByFecha(fecha: string): Promise<{ data: DimTiempo | null; error: Error | null }> {
    try {
      const { data, error } = await supabase
        .from('dim_tiempo')
        .select('*')
        .eq('fecha', fecha)
        .single()

      if (error) {
        console.error('Error fetching dim_tiempo by fecha:', error)
        return { data: null, error: new Error(error.message) }
      }

      return { data: data as DimTiempo, error: null }
    } catch (error) {
      console.error('Unexpected error:', error)
      return { 
        data: null, 
        error: error instanceof Error ? error : new Error('Unknown error occurred') 
      }
    }
  }

  async getByAnioMes(anio: number, mes: number): Promise<{ data: DimTiempo[] | null; error: Error | null }> {
    try {
      const { data, error } = await supabase
        .from('dim_tiempo')
        .select('*')
        .eq('anio', anio)
        .eq('mes', mes)
        .order('fecha', { ascending: true })

      if (error) {
        console.error('Error fetching dim_tiempo by anio/mes:', error)
        return { data: null, error: new Error(error.message) }
      }

      return { data: data as DimTiempo[], error: null }
    } catch (error) {
      console.error('Unexpected error:', error)
      return { 
        data: null, 
        error: error instanceof Error ? error : new Error('Unknown error occurred') 
      }
    }
  }

  async getByAnio(anio: number): Promise<{ data: DimTiempo[] | null; error: Error | null }> {
    try {
      const { data, error } = await supabase
        .from('dim_tiempo')
        .select('*')
        .eq('anio', anio)
        .order('fecha', { ascending: true })

      if (error) {
        console.error('Error fetching dim_tiempo by anio:', error)
        return { data: null, error: new Error(error.message) }
      }

      return { data: data as DimTiempo[], error: null }
    } catch (error) {
      console.error('Unexpected error:', error)
      return { 
        data: null, 
        error: error instanceof Error ? error : new Error('Unknown error occurred') 
      }
    }
  }

  async create(dimTiempo: Omit<DimTiempo, 'id' | 'created_at' | 'trimestre' | 'semestre'>): Promise<{ data: DimTiempo | null; error: Error | null }> {
    try {
      const { data, error } = await supabase
        .from('dim_tiempo')
        .insert(dimTiempo)
        .select()
        .single()

      if (error) {
        console.error('Error creating dim_tiempo:', error)
        return { data: null, error: new Error(error.message) }
      }

      return { data: data as DimTiempo, error: null }
    } catch (error) {
      console.error('Unexpected error:', error)
      return { 
        data: null, 
        error: error instanceof Error ? error : new Error('Unknown error occurred') 
      }
    }
  }

  async update(id: number, dimTiempo: Partial<Omit<DimTiempo, 'id' | 'trimestre' | 'semestre'>>): Promise<{ data: DimTiempo | null; error: Error | null }> {
    try {
      const { data, error } = await supabase
        .from('dim_tiempo')
        .update(dimTiempo)
        .eq('id', id)
        .select()
        .single()

      if (error) {
        console.error('Error updating dim_tiempo:', error)
        return { data: null, error: new Error(error.message) }
      }

      return { data: data as DimTiempo, error: null }
    } catch (error) {
      console.error('Unexpected error:', error)
      return { 
        data: null, 
        error: error instanceof Error ? error : new Error('Unknown error occurred') 
      }
    }
  }

  async delete(id: number): Promise<{ error: Error | null }> {
    try {
      const { error } = await supabase
        .from('dim_tiempo')
        .delete()
        .eq('id', id)

      if (error) {
        console.error('Error deleting dim_tiempo:', error)
        return { error: new Error(error.message) }
      }

      return { error: null }
    } catch (error) {
      console.error('Unexpected error:', error)
      return { 
        error: error instanceof Error ? error : new Error('Unknown error occurred') 
      }
    }
  }
}

export const dimTiempoService = DimTiempoService.getInstance()
