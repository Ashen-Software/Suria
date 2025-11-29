import { useState } from 'react'
import { DimTiempoViewer } from '@/components/DimTiempoViewer'
import { DimTerritoriosViewer } from '@/components/DimTerritoriosViewer'

type TabId = 'tiempo' | 'territorios' | 'areas'

const tabs: { id: TabId; label: string; helper: string }[] = [
  { id: 'tiempo', label: 'Dimensión Tiempo', helper: 'Calendario maestro' },
  { id: 'territorios', label: 'Dimensión Territorios', helper: 'Departamentos y municipios' },
  { id: 'areas', label: 'Áreas Eléctricas', helper: 'Ámbitos usados en proyecciones' },
]

export function DimensionesPage() {
  const [activeTab, setActiveTab] = useState<TabId>('tiempo')

  return (
    <div className="space-y-6">
      <section className="space-y-2">
        <p className="text-sm uppercase tracking-[0.2em] text-base-content/50">Catálogo maestro</p>
        <h2 className="text-gradient text-3xl font-semibold">Dimensiones del Modelo</h2>
        <p className="text-base text-base-content/70">
          Tiempo, territorios y demás dimensiones compartidas para los hechos de la plataforma Suria.
        </p>
      </section>

      <div className="glass-panel p-2">
        <div className="tabs tabs-boxed overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={`tab tab-sm sm:tab-md md:tab-lg whitespace-nowrap ${
                activeTab === tab.id ? 'tab-active' : ''
              }`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-6">
        {activeTab === 'tiempo' && <DimTiempoViewer />}
        {activeTab === 'territorios' && <DimTerritoriosViewer />}

        {activeTab === 'areas' && (
          <div className="glass-panel rounded-3xl p-6 space-y-2">
            <h3 className="text-lg font-semibold">Dimensión Áreas Eléctricas</h3>
            <p className="text-sm text-base-content/60">
              Catálogo de ámbitos y áreas eléctricas usados en las proyecciones de energía (SIN, áreas geográficas,
              etc.).
            </p>
            <p className="text-sm text-base-content/50">
              La visualización detallada de esta dimensión está pendiente de implementación.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}


