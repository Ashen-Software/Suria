import { useState } from 'react'

interface Document {
  title: string
  type: string
  download_url: string
  topics?: string[]
}

interface Section {
  id: string
  title: string
  description: string
  published_at: string
  documents: Document[]
  notes?: string[]
}

interface HistoricalItem {
  title: string
  type: string
  download_url: string
}

interface HistoricalYear {
  year: number
  items: HistoricalItem[]
  notes?: string
}

const upmeMetadata = {
  scraper: {
    id: 'proyeccion_upme',
    name: 'Proyección de demanda - UPME',
    source_url: 'https://www.upme.gov.co/simec/planeacion-energetica/proyeccion_de_demanda/',
    entity: 'Unidad de Planeación Minero-Energética (UPME)',
  },
  page_overview: {
    hero_title: 'Proyecciones de demanda',
    summary:
      'Ejercicio estadístico que combina consumo histórico con variables económicas y demográficas para estimar la demanda futura de energía eléctrica, gas natural y combustibles líquidos.',
    sections: [
      {
        id: 'intro_2025_2039',
        title: '¿Qué es? + Publicación base 2025-2039',
        description:
          'La UPME documenta los supuestos y modelos usados para proyectar la demanda nacional de energía eléctrica, gas natural y combustibles líquidos.',
        published_at: '2025-05-09',
        documents: [
          {
            title: 'Proyecciones de demanda 2025-2039 v4',
            type: 'pdf',
            download_url:
              'https://docs.upme.gov.co/DemandayEficiencia/Documents/Proyecciones_de_demanda_2025-2039_v4.pdf',
            topics: ['energia_electrica', 'proyeccion', 'metodologia'],
          },
        ],
        notes: [
          'Incluye narrativa completa del ejercicio y supuestos macroeconómicos.',
          'Publicado el 9 de mayo de 2025.',
        ],
      },
      {
        id: 'electricidad_2025_2039',
        title: 'Proyección de demanda de energía eléctrica y potencia máxima 2025-2039 (Rev. julio 2025)',
        description: 'Resultados nacionales y por área eléctrica con resolución anual y mensual.',
        published_at: '2025-05-09',
        documents: [
          {
            title: 'Reporte principal 2025-2039',
            type: 'pdf',
            download_url:
              'https://docs.upme.gov.co/DemandayEficiencia/Documents/Proyecciones_de_demanda_2025-2039_v4.pdf',
            topics: ['energia_electrica', 'potencia_maxima', 'series_mensuales'],
          },
          {
            title: 'Anexo – Resultados detallados 2025-2039',
            type: 'xlsx',
            download_url:
              'https://docs.upme.gov.co/DemandayEficiencia/Documents/Anexo_proyeccion_demanda_2025_2039_verJul2025.xlsx',
            topics: ['tabla_resumen', 'areas_electricas', 'mensualizacion'],
          },
        ],
        notes: [
          'Revisión publicada en julio 2025; misma URL que la publicación base.',
          'Anexo contiene series listas para ingestión y trazabilidad mensual vs anual.',
        ],
      },
      {
        id: 'analisis_el_nino_2024_2025',
        title: 'Análisis de demanda de energía eléctrica durante el fenómeno de El Niño',
        description:
          'Comparación entre revisiones de julio y diciembre 2023, destacando que el error cuadrático medio máximo fue 0,38%.',
        published_at: '2025-06-18',
        documents: [
          {
            title: 'Demanda de EE en fenómeno del Niño 2024-6-17 v2',
            type: 'pdf',
            download_url:
              'https://docs.upme.gov.co/DemandayEficiencia/Documents/Demanda_de_EE_en_fenomeno_del_Ni%C3%B1o_2024-6-17_v2.pdf',
            topics: ['fenomeno_el_nino', 'sensibilidad_demanda', 'series_historicas'],
          },
        ],
        notes: [
          'Incluye resumen ejecutivo y vínculos a tableros comparativos.',
          'Publicación del 18 de junio de 2025.',
        ],
      },
      {
        id: 'gas_natural_2024_2040',
        title: 'Escenarios de proyección de demanda de gas natural 2024-2040',
        description: 'Demanda esperada por sector y región, con escenarios alternativos de transición energética.',
        published_at: '2025-07-16',
        documents: [
          {
            title: 'Proyección de demanda de Gas Natural 2024-2038 (Rev. enero 2025)',
            type: 'pdf',
            download_url:
              'https://docs.upme.gov.co/DemandayEficiencia/Documents/Doc_Proyecc_Dem_Gas_Nat_Ene2025_v5.pdf',
            topics: ['gas_natural', 'escenarios', 'transicion_energetica'],
          },
          {
            title: 'Anexo – Datos Proyección Demanda Gas Natural 2024',
            type: 'zip',
            download_url:
              'https://docs.upme.gov.co/DemandayEficiencia/Documents/Anexo_Datos_Proyeccion_Demanda_Gas_Nat_2024.zip',
            topics: ['series_mensuales', 'nodos_gas', 'dataset_crudo'],
          },
        ],
        notes: [
          'Escenario medio proyecta crecimiento anual compuesto de 0,8% (sin sector eléctrico).',
          'Incluye escenarios alternativos para residencial, industrial, terciario y vehicular.',
        ],
      },
      {
        id: 'combustibles_liquidos_glp_2024_2040',
        title: 'Proyección de la demanda de combustibles líquidos y GLP 2024-2040',
        description: 'Demanda esperada de gasolina corriente/extra, ACPM, Jet Fuel y GLP con escenarios de sustitución.',
        published_at: '2025-04-07',
        documents: [
          {
            title: 'Proyecciones de demanda combustibles líquidos 2024-2040 (para comentarios)',
            type: 'pdf',
            download_url:
              'https://docs.upme.gov.co/DemandayEficiencia/Documents/UPME_Proyecciones_demanda_comb_liquidos_2024-2040_Para_comentarios_4-4-2025.pdf',
            topics: ['combustibles_liquidos', 'glp', 'escenarios_transicion'],
          },
          {
            title: 'Anexo – Proyección Demanda Combustibles Líquidos 2024-40',
            type: 'xlsx',
            download_url:
              'https://docs.upme.gov.co/Normatividad/Formato_matriz_de_comentarios_proyecciones_demanda_liquidos_y_GLP_2024-2040_cir_036-2025.xlsx',
            topics: ['formato_comentarios', 'datos_region', 'glp'],
          },
          {
            title: 'Formato comentarios proyección demanda líquidos 2024-2040',
            type: 'xlsx',
            download_url:
              'https://docs.upme.gov.co/Normatividad/Anexo_Proyeccion_demanda_combustibles_liquidos_2024-2040_comentarios_cir_036_2025.xlsx',
            topics: ['participacion_sector', 'validacion_externa'],
          },
        ],
        notes: [
          'Incluye escenarios específicos para transporte carretero y nuevos usos de GLP.',
          'Documentos orientados a consulta pública (abril 2025).',
        ],
      },
    ] as Section[],
  },
  historical_energy_electricity: [
    {
      year: 2024,
      items: [
        {
          title: 'Proyección demanda energía eléctrica y potencia máxima Rev. Jul 2024',
          type: 'pdf',
          download_url:
            'https://docs.upme.gov.co/DemandayEficiencia/Documents/Proyeccion_demanda_energia_electrica_y_potencia_maxima_rev_jul2024.pdf',
        },
        {
          title: 'Anexo proyección demanda 2024-2038 v2 Jul 2024',
          type: 'xlsx',
          download_url:
            'https://docs.upme.gov.co/DemandayEficiencia/Documents/Anexo_proyeccion_demanda_2024_2038_v2_Jul2024.xlsx',
        },
        {
          title: 'Proyecciones de Demanda Final (31-01-2024)',
          type: 'pdf',
          download_url:
            'https://docs.upme.gov.co/DemandayEficiencia/Documents/Proyecciones_de_Demanda_Final_v_31_01_2024.pdf',
        },
        {
          title: 'Resumen ejecutivo proyecciones demanda Rev. dic 2023',
          type: 'pdf',
          download_url:
            'https://docs.upme.gov.co/DemandayEficiencia/Documents/Resumen_ejecutivo_proyecciones_demanda_rev_dic_2023.pdf',
        },
        {
          title: 'Anexo proyección demanda energía eléctrica Rev. dic 2023',
          type: 'xlsx',
          download_url:
            'https://docs.upme.gov.co/DemandayEficiencia/Documents/Anexo_proyeccion_demanda_%20energia_electrica_rev_dic_2023.xlsx',
        },
        {
          title: 'Anexo proyección demanda gas natural Rev. dic 2023',
          type: 'zip',
          download_url:
            'https://docs.upme.gov.co/DemandayEficiencia/Documents/Anexo_proyeccion_demanda_gas_natural_rev_dic_2023.zip',
        },
      ],
      notes: 'Incluye actualización puente entre ejercicios 2023 y 2024.',
    },
    {
      year: 2023,
      items: [
        {
          title: 'Proyección demanda 2023-2037 (Revisión julio)',
          type: 'pdf',
          download_url:
            'https://docs.upme.gov.co/DemandayEficiencia/Documents/UPME_Proyeccion_demanda_2023-2037_VF2.pdf',
        },
        {
          title: 'Anexo proyección demanda EE 2023-2037',
          type: 'xlsx',
          download_url:
            'https://docs.upme.gov.co/DemandayEficiencia/Documents/Anexo_proyeccion_demanda_EE_2023_2037.xlsx',
        },
      ],
      notes: 'Documento principal más hojas de cálculo asociadas al PEI 2019-2022.',
    },
    {
      year: 2022,
      items: [
        {
          title: 'Anexo GCE Actualizado 2022',
          type: 'pdf',
          download_url:
            'https://docs.upme.gov.co/DemandayEficiencia/HistoricoproyeccionesEE/2022/Anexo_GCE_Actualizado_2022.pdf',
        },
        {
          title: 'Anexo GCE Actualizado 2022-2036 VF',
          type: 'xlsx',
          download_url:
            'https://docs.upme.gov.co/DemandayEficiencia/HistoricoproyeccionesEE/2022/Anexo_GCE_Actualizado_2022-2036_VF.xlsx',
        },
        {
          title: 'Informe proyección demanda energéticos Jun 2022',
          type: 'pdf',
          download_url:
            'https://docs.upme.gov.co/DemandayEficiencia/HistoricoproyeccionesEE/2022/Informe_proyeccion_demanda_energeticos_jun22.pdf',
        },
        {
          title: 'Anexo Proyección Demanda EE-GN-CL 2022-2036 VF Jun',
          type: 'xlsx',
          download_url:
            'https://docs.upme.gov.co/DemandayEficiencia/HistoricoproyeccionesEE/2022/Anexo_Proyeccion_Demanda_EE_GN_CL_2022-2036_VF_jun.xlsx',
        },
      ],
      notes: 'Documentos abarcan electricidad, gas natural y combustibles líquidos.',
    },
    {
      year: 2021,
      items: [
        {
          title: 'Proyección Demanda Energía Junio 2021',
          type: 'pdf',
          download_url:
            'https://docs.upme.gov.co/DemandayEficiencia/HistoricoproyeccionesEE/2021/UPME_Proyeccion_Demanda_Energia_Junio_2021.pdf',
        },
        {
          title: 'Tablas Proyección Demanda Energía Junio 2021',
          type: 'xlsx',
          download_url:
            'https://docs.upme.gov.co/DemandayEficiencia/HistoricoproyeccionesEE/2021/UPME_Tablas_Proyeccion_DE_Junio_2021.xlsx',
        },
      ],
      notes: 'Incluye tablas listas para consumo en procesos ETL.',
    },
    {
      year: 2020,
      items: [
        {
          title: 'Proyección Demanda Energía Junio 2020',
          type: 'pdf',
          download_url:
            'https://docs.upme.gov.co/DemandayEficiencia/HistoricoproyeccionesEE/2020/UPME_Proyeccion_Demanda_Energia_Junio_2020.pdf',
        },
        {
          title: 'Tablas Proyección Demanda Energía Junio 2020',
          type: 'xlsx',
          download_url:
            'https://docs.upme.gov.co/DemandayEficiencia/HistoricoproyeccionesEE/2020/UPME_Tablas_Proyeccion_DE_Junio_2020.xlsx',
        },
      ],
      notes: 'Base histórica mínima para reconstruir series desde 2020.',
    },
  ] as HistoricalYear[],
  interactive_resources: [
    {
      title: 'Dashboard Google Looker Studio',
      type: 'embed',
      url: 'https://lookerstudio.google.com/embed/reporting/7204226d-5cae-48ca-a261-c85745ffd102/page/iX4iB',
      description: 'Visualización interactiva con filtros por año y energético.',
      requires_authentication: false,
    },
  ],
  references: [
    'https://www.upme.gov.co/simec/planeacion-energetica/proyeccion_de_demanda/',
    'https://docs.upme.gov.co/DemandayEficiencia/Documents/Proyecciones_de_demanda_2025-2039_v4.pdf',
  ],
}

function getFileIcon(type: string) {
  switch (type.toLowerCase()) {
    case 'pdf':
      return '📄'
    case 'xlsx':
    case 'xls':
      return '📊'
    case 'zip':
      return '📦'
    default:
      return '📎'
  }
}

function CollapsibleSection({ section }: { section: Section }) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="glass-panel overflow-hidden rounded-2xl">
      <button
        className="flex w-full items-center justify-between p-6 text-left transition hover:bg-base-200/50"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex-1 space-y-2">
          <h3 className="text-lg font-semibold text-base-content">{section.title}</h3>
          <p className="text-sm text-base-content/70">{section.description}</p>
          <div className="flex items-center gap-2 text-xs text-base-content/60">
            <span>📅 Publicado: {section.published_at}</span>
            <span>•</span>
            <span>{section.documents.length} documento(s)</span>
          </div>
        </div>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className={`h-6 w-6 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="border-t border-base-200 p-6 space-y-4">
          {section.documents.map((doc, idx) => (
            <div key={idx} className="flex items-center justify-between rounded-xl bg-base-100/70 p-4">
              <div className="flex items-center gap-3 flex-1">
                <span className="text-2xl">{getFileIcon(doc.type)}</span>
                <div className="flex-1">
                  <p className="font-medium text-base-content">{doc.title}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="badge badge-sm badge-outline">{doc.type.toUpperCase()}</span>
                    {doc.topics && doc.topics.length > 0 && (
                      <span className="text-xs text-base-content/60">
                        {doc.topics.slice(0, 2).join(', ')}
                        {doc.topics.length > 2 && ` +${doc.topics.length - 2}`}
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <a
                href={doc.download_url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-primary btn-sm rounded-xl"
              >
                Abrir
              </a>
            </div>
          ))}

          {section.notes && section.notes.length > 0 && (
            <div className="mt-4 space-y-2">
              <p className="text-sm font-semibold text-base-content/70">Notas:</p>
              <ul className="list-disc list-inside space-y-1 text-sm text-base-content/60">
                {section.notes.map((note, idx) => (
                  <li key={idx}>{note}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function HistoricalYearSection({ yearData }: { yearData: HistoricalYear }) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="glass-panel overflow-hidden rounded-2xl">
      <button
        className="flex w-full items-center justify-between p-6 text-left transition hover:bg-base-200/50"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-base-content">Año {yearData.year}</h3>
          {yearData.notes && <p className="text-sm text-base-content/60 mt-1">{yearData.notes}</p>}
          <p className="text-xs text-base-content/50 mt-2">{yearData.items.length} documento(s) disponible(s)</p>
        </div>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className={`h-6 w-6 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="border-t border-base-200 p-6 space-y-3">
          {yearData.items.map((item, idx) => (
            <div key={idx} className="flex items-center justify-between rounded-xl bg-base-100/70 p-4">
              <div className="flex items-center gap-3 flex-1">
                <span className="text-2xl">{getFileIcon(item.type)}</span>
                <div>
                  <p className="font-medium text-base-content">{item.title}</p>
                  <span className="badge badge-sm badge-outline mt-1">{item.type.toUpperCase()}</span>
                </div>
              </div>
              <a
                href={item.download_url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-primary btn-sm rounded-xl"
              >
                Abrir
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export function UPMELanding() {
  return (
    <div className="space-y-6">
      {/* Hero Section */}
      <div className="glass-panel rounded-3xl p-8 space-y-4">
        <div className="space-y-2">
          <p className="text-sm uppercase tracking-[0.2em] text-base-content/50">Información General</p>
          <h2 className="text-gradient text-3xl font-semibold">{upmeMetadata.page_overview.hero_title}</h2>
          <p className="text-lg text-base-content/80">{upmeMetadata.page_overview.summary}</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-base-content/60">
          <span>🏛️ {upmeMetadata.scraper.entity}</span>
          <span>•</span>
          <a
            href={upmeMetadata.scraper.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="link link-hover"
          >
            Ver fuente original
          </a>
        </div>
      </div>

      {/* Secciones Principales */}
      <div className="space-y-4">
        <div className="space-y-2">
          <p className="text-sm uppercase tracking-[0.2em] text-base-content/50">Publicaciones Principales</p>
          <h3 className="text-xl font-semibold">Documentos y Proyecciones</h3>
        </div>
        <div className="space-y-3">
          {upmeMetadata.page_overview.sections.map((section) => (
            <CollapsibleSection key={section.id} section={section} />
          ))}
        </div>
      </div>

      {/* Recursos Históricos */}
      <div className="space-y-4">
        <div className="space-y-2">
          <p className="text-sm uppercase tracking-[0.2em] text-base-content/50">Histórico</p>
          <h3 className="text-xl font-semibold">Proyecciones Anteriores</h3>
        </div>
        <div className="space-y-3">
          {upmeMetadata.historical_energy_electricity.map((yearData) => (
            <HistoricalYearSection key={yearData.year} yearData={yearData} />
          ))}
        </div>
      </div>

      {/* Referencias */}
      <div className="glass-panel rounded-2xl p-6 space-y-2">
        <p className="text-sm font-semibold text-base-content/70">Referencias</p>
        <ul className="list-disc list-inside space-y-1 text-sm text-base-content/60">
          {upmeMetadata.references.map((ref, idx) => (
            <li key={idx}>
              <a href={ref} target="_blank" rel="noopener noreferrer" className="link link-hover">
                {ref}
              </a>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

