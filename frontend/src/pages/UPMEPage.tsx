import { useState } from 'react';
import { EnergiaElectricaCharts } from '@/components/upme/EnergiaElectricaCharts';
import { PotenciaMaximaCharts } from '@/components/upme/PotenciaMaximaCharts';
import { CapacidadInstaladaCharts } from '@/components/upme/CapacidadInstaladaCharts';
import { GasNaturalCharts } from '@/components/upme/GasNaturalCharts';
import { UPMELanding } from '@/components/upme/UPMELanding';

type TabType = 'info' | 'energia' | 'potencia' | 'capacidad' | 'gas' | 'looker';

const tabs: { id: TabType; label: string; icon: string }[] = [
  { id: 'info', label: 'Información', icon: '📋' },
  { id: 'gas', label: 'Gas Natural', icon: '🔥' },
  { id: 'energia', label: 'Energía Eléctrica', icon: '⚡' },
  { id: 'potencia', label: 'Potencia Máxima', icon: '📊' },
  { id: 'capacidad', label: 'Capacidad Instalada', icon: '🏭' },
  { id: 'looker', label: 'Proyección de la demanda', icon: '📈' },
];

export function UPMEPage() {
  const [activeTab, setActiveTab] = useState<TabType>('info');

  return (
    <div className="space-y-6">
      <section className="space-y-4">
        <div className="space-y-2">
          <p className="text-sm uppercase tracking-[0.2em] text-base-content/50">Visualización</p>
          <h2 className="text-gradient text-3xl font-semibold">Dashboard UPME</h2>
          <p className="text-base text-base-content/70">
            Proyecciones de demanda energética de la Unidad de Planeación Minero Energética
          </p>
        </div>
      </section>

      {/* Tabs */}
      <div className="glass-panel p-2">
        <div className="tabs tabs-boxed">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={`tab tab-lg ${activeTab === tab.id ? 'tab-active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Contenido de tabs */}
      <div className="space-y-6">
        {activeTab === 'info' && <UPMELanding />}
        {activeTab === 'energia' && <EnergiaElectricaCharts />}
        {activeTab === 'potencia' && <PotenciaMaximaCharts />}
        {activeTab === 'capacidad' && <CapacidadInstaladaCharts />}
        {activeTab === 'gas' && <GasNaturalCharts />}
        {activeTab === 'looker' && (
          <div className="glass-panel overflow-hidden p-6">
            <div className="space-y-4">
              <div className="alert alert-info">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" className="stroke-current shrink-0 w-6 h-6">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <div>
                  <h3 className="font-bold">Nota sobre Looker Studio</h3>
                  <div className="text-xs">
                    Si el reporte no se muestra, puede ser que necesite estar configurado para compartirse públicamente. 
                    Usa el enlace de abajo para abrirlo directamente en Looker Studio.
                  </div>
                </div>
              </div>
              <div className="relative w-full mx-auto max-w-7xl" style={{ minHeight: '600px', height: '600px' }}>
                <iframe
                  src="https://lookerstudio.google.com/embed/reporting/7204226d-5cae-48ca-a261-c85745ffd102/page/iX4iB"
                  className="absolute inset-0 w-full h-full border-0 rounded-2xl"
                  allowFullScreen
                  title="Proyección de la demanda - Looker Studio"
                  loading="lazy"
                  style={{ border: 'none' }}
                  allow="fullscreen"
                />
                <div className="absolute bottom-4 right-4 bg-base-100/90 backdrop-blur-sm px-3 py-2 rounded-lg shadow-lg z-10">
                  <a 
                    href="https://lookerstudio.google.com/reporting/7204226d-5cae-48ca-a261-c85745ffd102/page/iX4iB" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="link link-hover text-sm font-semibold"
                  >
                    Abrir en Looker Studio ↗
                  </a>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
