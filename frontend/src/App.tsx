import { Routes, Route } from 'react-router'
import { useEtlSources } from '@/hooks/useEtlSources'
import { EtlSourceList } from '@/components/EtlSourceList'
import { TestPage } from '@/pages/TestPage'

function HomePage() {
  const { etlSources, loading, error } = useEtlSources()

  return <EtlSourceList etlSources={etlSources} loading={loading} error={error} />
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
