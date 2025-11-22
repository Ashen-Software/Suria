
import { useState, useEffect } from 'react'
import supabase from './utils/supabase'

function Page() {
  const [productos, setProductos] = useState<any[]>([])

  useEffect(() => {
    async function getProductos() {
      const { data: productosData, error } = await supabase.from('productos').select()
      if (error) {
        console.error('Supabase error fetching productos:', error)
        return
      }

      if (Array.isArray(productosData) && productosData.length > 0) {
        setProductos(productosData)
      }
    }

    getProductos()
  }, [])
  return (
    <div className="p-4">
      <ul className="list bg-base-100 rounded-box shadow-md">
        {productos.map((producto, index) => (
          <li key={index} className="list-row">{typeof producto === 'object' ? JSON.stringify(producto) : String(producto)}</li>
        ))}
      </ul>
    </div>
  )
}

export default Page
