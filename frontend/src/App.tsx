import { Routes, Route } from 'react-router'
import { EtlSourceManager } from '@/components/EtlSourceManager'
import { TestPage } from '@/pages/TestPage'
import { HomePage } from '@/pages/Home'

function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/manager" element={<EtlSourceManager />} />
      <Route path="/test" element={<TestPage />} />
    </Routes>
  )
}

export default App
