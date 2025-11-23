
import { useProductos } from '@/hooks/useProductos'
import { ProductoList } from '@/components/ProductoList'

function Page() {
  const { productos, loading, error } = useProductos()

  return <ProductoList productos={productos} loading={loading} error={error} />
}

export default Page
