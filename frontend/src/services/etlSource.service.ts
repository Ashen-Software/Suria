import { supabase } from '@/config/supabase'
import type { EtlSource } from '@/types/etlSource.types';

export class EtlSourceService {
  private static instance: EtlSourceService

  private constructor() {}

  static getInstance(): EtlSourceService {
    if (!EtlSourceService.instance) {
      EtlSourceService.instance = new EtlSourceService()
    }
    return EtlSourceService.instance
  }

  async getAll(params?: { 
    page?: number; 
    pageSize?: number 
  }): Promise<{ 
    data: EtlSource[] | null; 
    error: Error | null;
    count: number | null;
  }> {
    try {
      const page = params?.page ?? 0
      const pageSize = params?.pageSize ?? 10
      const from = page * pageSize
      const to = from + pageSize - 1

      const { data, error, count } = await supabase
        .from('etl_sources')
        .select('*', { count: 'exact' })
        .order('created_at', { ascending: false })
        .range(from, to)

      if (error) {
        console.error('Error fetching etl_sources:', error)
        return { data: null, error: new Error(error.message), count: null }
      }

      return { data: data as EtlSource[], error: null, count: count ?? 0 }
    } catch (error) {
      console.error('Unexpected error:', error)
      return { 
        data: null, 
        error: error instanceof Error ? error : new Error('Unknown error occurred'),
        count: null
      }
    }
  }

  async getById(id: string): Promise<{ data: EtlSource | null; error: Error | null }> {
    try {
      const { data, error } = await supabase
        .from('etl_sources')
        .select('*')
        .eq('id', id)
        .single()

      if (error) {
        console.error('Error fetching etl_source:', error)
        return { data: null, error: new Error(error.message) }
      }

      return { data: data as EtlSource, error: null }
    } catch (error) {
      console.error('Unexpected error:', error)
      return { 
        data: null, 
        error: error instanceof Error ? error : new Error('Unknown error occurred') 
      }
    }
  }

  async create(etlSource: Omit<EtlSource, 'id' | 'created_at' | 'updated_at'>): Promise<{ data: EtlSource | null; error: Error | null }> {
    try {
      const { data, error } = await supabase
        .from('etl_sources')
        .insert(etlSource)
        .select()
        .single()

      if (error) {
        console.error('Error creating etl_source:', error)
        return { data: null, error: new Error(error.message) }
      }

      return { data: data as EtlSource, error: null }
    } catch (error) {
      console.error('Unexpected error:', error)
      return { 
        data: null, 
        error: error instanceof Error ? error : new Error('Unknown error occurred') 
      }
    }
  }

  async update(id: string, etlSource: Partial<EtlSource>): Promise<{ data: EtlSource | null; error: Error | null }> {
    try {
      const { data, error } = await supabase
        .from('etl_sources')
        .update(etlSource)
        .eq('id', id)
        .select()
        .single()

      if (error) {
        console.error('Error updating etl_source:', error)
        return { data: null, error: new Error(error.message) }
      }

      return { data: data as EtlSource, error: null }
    } catch (error) {
      console.error('Unexpected error:', error)
      return { 
        data: null, 
        error: error instanceof Error ? error : new Error('Unknown error occurred') 
      }
    }
  }

  async delete(id: string): Promise<{ error: Error | null }> {
    try {
      const { error } = await supabase
        .from('etl_sources')
        .delete()
        .eq('id', id)

      if (error) {
        console.error('Error deleting etl_source:', error)
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

export const etlSourceService = EtlSourceService.getInstance()
