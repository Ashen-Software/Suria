import { Routes, Route } from 'react-router'
import { MainLayout } from '@/components/layout/MainLayout'
import { HomePage } from '@/pages/Home'
import { EtlSourcePage } from '@/pages/EtlSourcePage'
import { DimTerritoriosPage } from '@/pages/DimTerritoriosPage'
import { DimensionesPage } from '@/pages/DimensionesPage'
import { UPMEPage } from '@/pages/UPMEPage'
import { DeclaracionGasPage, RegaliasPage } from '@/pages/DeclaracionRegaliasPage'
import { IntegradoPage } from '@/pages/IntegradoPage'

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/integrado" element={<IntegradoPage />} />
        <Route path="/admin" element={<EtlSourcePage />} />
        <Route path="/dimensiones" element={<DimensionesPage />} />
        {/* Ruta directa a territorios si la necesitas sin tabs */}
        <Route path="/territorios" element={<DimTerritoriosPage />} />
        <Route path="/upme" element={<UPMEPage />} />
        <Route path="/declaracion-gas" element={<DeclaracionGasPage />} />
        <Route path="/regalias" element={<RegaliasPage />} />
      </Route>
    </Routes>
  )
}
