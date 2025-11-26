import { Routes, Route } from 'react-router'
import { MainLayout } from '@/components/layout/MainLayout'
import { HomePage } from '@/pages/Home'
import { EtlSourceManager } from '@/components/EtlSourceManager'
import { TestPage } from '@/pages/TestPage'

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/manager" element={<EtlSourceManager />} />
        <Route path="/test" element={<TestPage />} />
      </Route>
    </Routes>
  )
}
