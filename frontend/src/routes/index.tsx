import { Routes, Route } from 'react-router'
import { MainLayout } from '@/components/layout/MainLayout'
import { HomePage } from '@/pages/Home'
import { EtlSourcePage } from '@/pages/EtlSourcePage'
import { DimTiempoPage } from '@/pages/DimTiempoPage'
import { DimTerritoriosPage } from '@/pages/DimTerritoriosPage'
import { UPMEPage } from '@/pages/UPMEPage'

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/admin" element={<EtlSourcePage />} />
        <Route path="/tiempo" element={<DimTiempoPage />} />
        <Route path="/territorios" element={<DimTerritoriosPage />} />
        <Route path="/upme" element={<UPMEPage />} />
      </Route>
    </Routes>
  )
}
