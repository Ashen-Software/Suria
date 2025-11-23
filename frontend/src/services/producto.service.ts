import { supabase } from '@/config/supabase'
import type { Producto } from '@/types/producto.types';

export class ProductoService {
  private static instance: ProductoService

  private constructor() {}

  static getInstance(): ProductoService {
    if (!ProductoService.instance) {
      ProductoService.instance = new ProductoService()
    }
    return ProductoService.instance
  }

  async getAll(): Promise<{ data: Producto[] | null; error: Error | null }> {
    try {
      const { data, error } = await supabase
        .from('productos')
        .select('*')
        .order('created_at', { ascending: false })

      if (error) {
        console.error('Error fetching productos:', error)
        return { data: null, error: new Error(error.message) }
      }

      return { data: data as Producto[], error: null }
    } catch (error) {
      console.error('Unexpected error:', error)
      return { 
        data: null, 
        error: error instanceof Error ? error : new Error('Unknown error occurred') 
      }
    }
  }

  async getById(id: string): Promise<{ data: Producto | null; error: Error | null }> {
    try {
      const { data, error } = await supabase
        .from('productos')
        .select('*')
        .eq('id', id)
        .single()

      if (error) {
        console.error('Error fetching producto:', error)
        return { data: null, error: new Error(error.message) }
      }

      return { data: data as Producto, error: null }
    } catch (error) {
      console.error('Unexpected error:', error)
      return { 
        data: null, 
        error: error instanceof Error ? error : new Error('Unknown error occurred') 
      }
    }
  }

  async create(producto: Omit<Producto, 'id' | 'created_at' | 'updated_at'>): Promise<{ data: Producto | null; error: Error | null }> {
    try {
      const { data, error } = await supabase
        .from('productos')
        .insert(producto)
        .select()
        .single()

      if (error) {
        console.error('Error creating producto:', error)
        return { data: null, error: new Error(error.message) }
      }

      return { data: data as Producto, error: null }
    } catch (error) {
      console.error('Unexpected error:', error)
      return { 
        data: null, 
        error: error instanceof Error ? error : new Error('Unknown error occurred') 
      }
    }
  }

  async update(id: string, producto: Partial<Producto>): Promise<{ data: Producto | null; error: Error | null }> {
    try {
      const { data, error } = await supabase
        .from('productos')
        .update(producto)
        .eq('id', id)
        .select()
        .single()

      if (error) {
        console.error('Error updating producto:', error)
        return { data: null, error: new Error(error.message) }
      }

      return { data: data as Producto, error: null }
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
        .from('productos')
        .delete()
        .eq('id', id)

      if (error) {
        console.error('Error deleting producto:', error)
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

export const productoService = ProductoService.getInstance()
