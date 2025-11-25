import { Routes, Route } from 'react-router'
import { useProductos } from '@/hooks/useProductos'
import { ProductoList } from '@/components/ProductoList'
import { TestPage } from '@/pages/TestPage'

function HomePage() {
  const { productos, loading, error } = useProductos()

  return <ProductoList productos={productos} loading={loading} error={error} />
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/test" element={<TestPage />} />
    </Routes>
  )
}

export default App
