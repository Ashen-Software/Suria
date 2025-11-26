import { Routes, Route } from 'react-router'
import { EtlSourceList } from '@/components/EtlSourceList'
import { TestPage } from '@/pages/TestPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<EtlSourceList />} />
      <Route path="/test" element={<TestPage />} />
    </Routes>
  )
}

export default App
