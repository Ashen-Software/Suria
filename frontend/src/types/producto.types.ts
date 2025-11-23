export interface Producto {
  id: string
  nombre: string
  created_at?: string
  updated_at?: string
}

export interface ProductoFormData extends Omit<Producto, 'id' | 'created_at' | 'updated_at'> {}
