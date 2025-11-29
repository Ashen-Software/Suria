import { useEffect, useMemo, useRef, useState } from 'react'
import { useInfiniteQuery } from '@tanstack/react-query'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts'
import type { OfertaGasRecord, RegaliasRecord } from '@/types/declaracion_regalias.types'
import type { EnergiaElectricaRecord, GasNaturalRecord } from '@/types/upme.types'
import { loadOfertaGasPage, loadRegaliasPage } from '@/services/declaracionRegaliasData.service'
import { loadEnergiaElectricaPage, loadGasNaturalPage } from '@/services/upmeData.service'
import { createLLMService } from '@/services/llm.service'
import type { ChatContext, Message } from '@/types/chatbot.types'

const API_PAGE_SIZE = 5000

interface BalancePoint {
  year: string
  demanda_gas: number
  oferta_gas: number
  brecha: number
}

interface RegaliasYearPoint {
  year: string
  total: number
  gas: number
}

export function IntegradoPage() {
  const [analysis, setAnalysis] = useState<string | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [allowEarlyAnalysis, setAllowEarlyAnalysis] = useState(false)
  const [remainingSeconds, setRemainingSeconds] = useState(60)
  const llmServiceRef = useRef(createLLMService({ temperature: 0.3, maxTokens: 900 }))

  // Demanda gas (UPME)
  const demandaGasQuery = useInfiniteQuery<GasNaturalRecord[]>({
    queryKey: ['integrado-demanda-gas'],
    queryFn: async ({ pageParam }) =>
      loadGasNaturalPage((pageParam as number) ?? 0, API_PAGE_SIZE),
    getNextPageParam: (lastPage, allPages) =>
      lastPage.length === API_PAGE_SIZE ? allPages.length : undefined,
    initialPageParam: 0,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  })

  // Demanda eléctrica (UPME)
  const energiaQuery = useInfiniteQuery<EnergiaElectricaRecord[]>({
    queryKey: ['integrado-energia-electrica'],
    queryFn: async ({ pageParam }) =>
      loadEnergiaElectricaPage((pageParam as number) ?? 0, API_PAGE_SIZE),
    getNextPageParam: (lastPage, allPages) =>
      lastPage.length === API_PAGE_SIZE ? allPages.length : undefined,
    initialPageParam: 0,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  })

  // Oferta gas (Declaración)
  const ofertaQuery = useInfiniteQuery<OfertaGasRecord[]>({
    queryKey: ['integrado-oferta-gas'],
    queryFn: async ({ pageParam }) =>
      loadOfertaGasPage((pageParam as number) ?? 0, API_PAGE_SIZE),
    getNextPageParam: (lastPage, allPages) =>
      lastPage.length === API_PAGE_SIZE ? allPages.length : undefined,
    initialPageParam: 0,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  })

  // Regalías (ANH)
  const regaliasQuery = useInfiniteQuery<RegaliasRecord[]>({
    queryKey: ['integrado-regalias'],
    queryFn: async ({ pageParam }) =>
      loadRegaliasPage((pageParam as number) ?? 0, API_PAGE_SIZE),
    getNextPageParam: (lastPage, allPages) =>
      lastPage.length === API_PAGE_SIZE ? allPages.length : undefined,
    initialPageParam: 0,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  })

  // Carga automática de todas las páginas para cada fuente
  useEffect(() => {
    if (demandaGasQuery.hasNextPage && !demandaGasQuery.isFetchingNextPage) {
      demandaGasQuery.fetchNextPage()
    }
  }, [demandaGasQuery.hasNextPage, demandaGasQuery.isFetchingNextPage, demandaGasQuery.fetchNextPage])

  useEffect(() => {
    if (energiaQuery.hasNextPage && !energiaQuery.isFetchingNextPage) {
      energiaQuery.fetchNextPage()
    }
  }, [energiaQuery.hasNextPage, energiaQuery.isFetchingNextPage, energiaQuery.fetchNextPage])

  useEffect(() => {
    if (ofertaQuery.hasNextPage && !ofertaQuery.isFetchingNextPage) {
      ofertaQuery.fetchNextPage()
    }
  }, [ofertaQuery.hasNextPage, ofertaQuery.isFetchingNextPage, ofertaQuery.fetchNextPage])

  useEffect(() => {
    if (regaliasQuery.hasNextPage && !regaliasQuery.isFetchingNextPage) {
      regaliasQuery.fetchNextPage()
    }
  }, [regaliasQuery.hasNextPage, regaliasQuery.isFetchingNextPage, regaliasQuery.fetchNextPage])

  const flatDemandaGas: GasNaturalRecord[] = useMemo(
    () => ((demandaGasQuery.data?.pages as GasNaturalRecord[][]) ?? []).flat(),
    [demandaGasQuery.data],
  )

  const flatEnergia: EnergiaElectricaRecord[] = useMemo(
    () => ((energiaQuery.data?.pages as EnergiaElectricaRecord[][]) ?? []).flat(),
    [energiaQuery.data],
  )

  const flatOferta: OfertaGasRecord[] = useMemo(
    () => ((ofertaQuery.data?.pages as OfertaGasRecord[][]) ?? []).flat(),
    [ofertaQuery.data],
  )

  const flatRegalias: RegaliasRecord[] = useMemo(
    () => ((regaliasQuery.data?.pages as RegaliasRecord[][]) ?? []).flat(),
    [regaliasQuery.data],
  )

  const isLoadingAll =
    demandaGasQuery.isLoading ||
    energiaQuery.isLoading ||
    ofertaQuery.isLoading ||
    regaliasQuery.isLoading

  const hasAnyError =
    demandaGasQuery.error ||
    energiaQuery.error ||
    ofertaQuery.error ||
    regaliasQuery.error

  // KPIs integrados
  const {
    demandaTotalGas,
    demandaTotalElectricidad,
    ofertaTotalGas,
    regaliasAcumuladas,
  } = useMemo(() => {
    const demandaGas = flatDemandaGas
      .filter((r) => r.escenario === 'ESC_MEDIO')
      .reduce((sum, r) => sum + (Number(r.valor) || 0), 0)

    const demandaElec = flatEnergia
      .filter((r) => r.escenario === 'ESC_MEDIO')
      .reduce((sum, r) => sum + (Number(r.valor) || 0), 0)

    const ofertaGas = flatOferta.reduce((sum, r) => sum + (Number(r.valor_gbtud) || 0), 0)

    const regalias = flatRegalias.reduce(
      (sum, r) => sum + (Number(r.valor_regalias_cop) || 0),
      0,
    )

    return {
      demandaTotalGas: demandaGas,
      demandaTotalElectricidad: demandaElec,
      ofertaTotalGas: ofertaGas,
      regaliasAcumuladas: regalias,
    }
  }, [flatDemandaGas, flatEnergia, flatOferta, flatRegalias])

  // Serie oferta vs demanda (anual, escenario medio)
  const balanceOfertaDemanda: BalancePoint[] = useMemo(() => {
    if (!flatDemandaGas.length && !flatOferta.length) return []

    const demandaPorAnio = new Map<string, number>()
    flatDemandaGas
      .filter((r) => r.escenario === 'ESC_MEDIO' && r.periodicidad === 'mensual')
      .forEach((r) => {
        const year = r.period_key.split('-')[0]
        demandaPorAnio.set(year, (demandaPorAnio.get(year) || 0) + (Number(r.valor) || 0))
      })

    const ofertaPorAnio = new Map<string, number>()
    flatOferta.forEach((r) => {
      const year = r.period_key.split('-')[0]
      ofertaPorAnio.set(year, (ofertaPorAnio.get(year) || 0) + (Number(r.valor_gbtud) || 0))
    })

    const years = Array.from(
      new Set([...demandaPorAnio.keys(), ...ofertaPorAnio.keys()]),
    ).sort((a, b) => Number(a) - Number(b))

    return years.map((year) => {
      const demanda = demandaPorAnio.get(year) || 0
      const oferta = ofertaPorAnio.get(year) || 0
      return {
        year,
        demanda_gas: demanda,
        oferta_gas: oferta,
        brecha: oferta - demanda,
      }
    })
  }, [flatDemandaGas, flatOferta])

  // Serie de regalías anuales (totales y solo gas)
  const regalíasPorAnio: RegaliasYearPoint[] = useMemo(() => {
    if (!flatRegalias.length) return []

    const totalPorAnio = new Map<string, number>()
    const gasPorAnio = new Map<string, number>()

    flatRegalias.forEach((r) => {
      if (!r.period_key) return
      const year = r.period_key.split('-')[0]
      const valor = Number(r.valor_regalias_cop) || 0
      totalPorAnio.set(year, (totalPorAnio.get(year) || 0) + valor)

      if (r.tipo_hidrocarburo && r.tipo_hidrocarburo.toLowerCase().includes('gas')) {
        gasPorAnio.set(year, (gasPorAnio.get(year) || 0) + valor)
      }
    })

    const years = Array.from(totalPorAnio.keys()).sort((a, b) => Number(a) - Number(b))

    return years
      .map((year) => ({
        year,
        total: totalPorAnio.get(year) || 0,
        gas: gasPorAnio.get(year) || 0,
      }))
      // Mantener años recientes y con datos reales
      .filter((p) => {
        const y = Number(p.year)
        return y >= 2000 && y <= 2100 && p.total > 0
      })
  }, [flatRegalias])

  // Tabla integrada por año
  const tablaIntegrada = useMemo(() => {
    if (!balanceOfertaDemanda.length && !flatEnergia.length && !regalíasPorAnio.length) return []

    // Demanda eléctrica anual (ESC_MEDIO)
    const energiaPorAnio = new Map<string, number>()
    flatEnergia
      .filter((r) => r.escenario === 'ESC_MEDIO')
      .forEach((r) => {
        const year = r.period_key.split('-')[0]
        energiaPorAnio.set(year, (energiaPorAnio.get(year) || 0) + (Number(r.valor) || 0))
      })

    const regaliasMap = new Map<string, number>()
    regalíasPorAnio.forEach((p) => {
      regaliasMap.set(p.year, p.total)
    })

    const balanceMap = new Map<string, BalancePoint>()
    balanceOfertaDemanda.forEach((p) => {
      balanceMap.set(p.year, p)
    })

    const years = Array.from(
      new Set([
        ...Array.from(balanceMap.keys()),
        ...Array.from(energiaPorAnio.keys()),
        ...Array.from(regaliasMap.keys()),
      ]),
    ).sort((a, b) => Number(a) - Number(b))

    return years
      .map((year) => {
        const balance = balanceMap.get(year)
        const demandaGas = balance?.demanda_gas ?? 0
        const ofertaGas = balance?.oferta_gas ?? 0
        const brecha = balance?.brecha ?? ofertaGas - demandaGas
        const demandaElec = energiaPorAnio.get(year) || 0
        const regalias = regaliasMap.get(year) || 0

        return {
          year,
          demandaGas,
          ofertaGas,
          brecha,
          demandaElec,
          regalias,
        }
      })
      // Filtrar años fuera de rango o completamente vacíos
      .filter((row) => {
        const y = Number(row.year)
        const hasAnyValue =
          row.demandaGas !== 0 ||
          row.ofertaGas !== 0 ||
          row.brecha !== 0 ||
          row.demandaElec !== 0 ||
          row.regalias !== 0

        return y >= 2000 && y <= 2100 && hasAnyValue
      })
  }, [balanceOfertaDemanda, flatEnergia, regalíasPorAnio])

  // Flag para permitir análisis aunque no se hayan cargado todas las páginas (después de 1 minuto)
  useEffect(() => {
    if (allowEarlyAnalysis) {
      return
    }

    const interval = setInterval(() => {
      setRemainingSeconds((prev) => {
        if (prev <= 1) {
          clearInterval(interval)
          setAllowEarlyAnalysis(true)
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(interval)
  }, [allowEarlyAnalysis])

  const allPagesLoaded =
    demandaGasQuery.hasNextPage === false &&
    energiaQuery.hasNextPage === false &&
    ofertaQuery.hasNextPage === false &&
    regaliasQuery.hasNextPage === false

  const isButtonDisabled =
    isAnalyzing ||
    ((!allPagesLoaded && !allowEarlyAnalysis) ||
      (!tablaIntegrada.length && !balanceOfertaDemanda.length))

  const buttonTooltip =
    !allPagesLoaded && !allowEarlyAnalysis
      ? `El botón se desbloqueará automáticamente en ${remainingSeconds}s o cuando terminen de cargarse todas las páginas de datos.`
      : !allPagesLoaded && allowEarlyAnalysis
        ? 'Algunos datos siguen cargando; el análisis se generará con la información disponible hasta ahora.'
        : ''

  const handleGenerateAnalysis = async () => {
    try {
      setIsAnalyzing(true)

      const context: ChatContext = {
        currentRoute: '/integrado',
        routeName: 'Integrado',
        availableData: {
          territorios: false,
          tiempo: true,
          etlSources: false,
        },
        appInfo: {
          name: 'Suria',
          version: '1.0.0',
          description:
            'Dashboard integrado de demanda y oferta de gas, demanda eléctrica y regalías del sector energético colombiano.',
        },
      }

      const payload = {
        kpis: {
          demandaTotalGas,
          demandaTotalElectricidad,
          ofertaTotalGas,
          regaliasAcumuladas,
        },
        balanceOfertaDemanda: balanceOfertaDemanda.slice(-15),
        regaliasPorAnio: regalíasPorAnio.slice(-15),
        resumenTabla: tablaIntegrada.slice(-15),
      }

      const userMessage: Message = {
        id: 'integrado-ia',
        role: 'user',
        content: `Estás analizando el dashboard integrado del sistema energético colombiano.

Datos agregados (formato JSON):
${JSON.stringify(payload)}

Con base en estos datos numéricos:
- Cita explícitamente los valores de los KPIs (demandaTotalGas, demandaTotalElectricidad, ofertaTotalGas, regaliasAcumuladas) con sus unidades.
- Usa los campos year, demanda_gas, oferta_gas y brecha de balanceOfertaDemanda para mencionar años concretos donde la oferta supera a la demanda y años donde la brecha es muy negativa.
- Usa los campos year y total de regaliasPorAnio para señalar años de máximo y de caída de regalías.
- Puedes apoyarte también en resumenTabla (por ejemplo, años con mayor demandaEléctrica o mayores regalias).
- Explica en español, de forma ejecutiva, cómo se relacionan la demanda de gas (UPME, ESC_MEDIO), la oferta de gas (declaración) y las regalías, incluyendo posibles implicaciones.
- Añade un bloque claramente marcado como "Análisis predictivo" donde, apoyándote en las tendencias históricas de las series, describas cómo podría verse el sistema en los próximos años (por ejemplo, si la brecha oferta-demanda tendería a ampliarse o reducirse, y qué impacto tendría en las regalías), dejando claro que es un ejercicio de proyección cualitativa, no un pronóstico exacto.
- Usa 3 a 5 párrafos cortos, sin viñetas, y evita lenguaje demasiado técnico.`,
        timestamp: new Date(),
      }

      const response = await llmServiceRef.current.sendMessage([userMessage], context)
      setAnalysis(response)
    } catch (error) {
      console.error('Error generando análisis con IA:', error)
      setAnalysis(
        'No se pudo generar el análisis con IA en este momento. Intenta de nuevo más tarde o revisa la configuración de la API.',
      )
    } finally {
      setIsAnalyzing(false)
    }
  }

  if (hasAnyError) {
    return (
      <div className="alert alert-error">
        <span>Error al cargar datos integrados de gas, electricidad y regalías.</span>
      </div>
    )
  }

  if (isLoadingAll && !flatDemandaGas.length && !flatEnergia.length && !flatOferta.length && !flatRegalias.length) {
    return (
      <div className="space-y-6">
        <div className="glass-panel p-6 animate-pulse space-y-4">
          <div className="h-6 w-64 rounded-xl bg-base-300" />
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="h-24 rounded-2xl bg-base-300" />
            <div className="h-24 rounded-2xl bg-base-300" />
            <div className="h-24 rounded-2xl bg-base-300" />
            <div className="h-24 rounded-2xl bg-base-300" />
          </div>
        </div>
        <div className="glass-panel p-6 animate-pulse space-y-4">
          <div className="h-6 w-72 rounded-xl bg-base-300" />
          <div className="h-80 rounded-3xl bg-base-300" />
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <section className="glass-panel p-6 space-y-4">
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <h3 className="text-xl font-semibold">Visión integrada del sistema energético</h3>
            <p className="text-sm text-base-content/70">
              Demanda y oferta de gas, demanda eléctrica y regalías consolidadas en un solo panel.
            </p>
          </div>
          <div
            className={buttonTooltip ? 'tooltip tooltip-left' : ''}
            data-tip={buttonTooltip || undefined}
          >
            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={handleGenerateAnalysis}
              disabled={isButtonDisabled}
            >
              {isAnalyzing ? 'Generando análisis con IA...' : 'Generar análisis con IA'}
              {isAnalyzing && <span className="loading loading-spinner loading-xs ml-2" />}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-2">
          <div className="stat rounded-2xl bg-base-200/60">
            <div className="stat-title text-xs uppercase tracking-[0.2em]">
              Demanda total gas (ESC_MEDIO)
            </div>
            <div className="stat-value text-primary text-lg">
              {demandaTotalGas.toLocaleString('es-ES', {
                maximumFractionDigits: 0,
              })}{' '}
              <span className="text-base text-base-content/70">GBTUD</span>
            </div>
          </div>

          <div className="stat rounded-2xl bg-base-200/60">
            <div className="stat-title text-xs uppercase tracking-[0.2em]">
              Demanda total electricidad (ESC_MEDIO)
            </div>
            <div className="stat-value text-secondary text-lg">
              {demandaTotalElectricidad.toLocaleString('es-ES', {
                maximumFractionDigits: 0,
              })}{' '}
              <span className="text-base text-base-content/70">GWh</span>
            </div>
          </div>

          <div className="stat rounded-2xl bg-base-200/60">
            <div className="stat-title text-xs uppercase tracking-[0.2em]">
              Oferta total gas (declaración)
            </div>
            <div className="stat-value text-accent text-lg">
              {ofertaTotalGas.toLocaleString('es-ES', {
                maximumFractionDigits: 0,
              })}{' '}
              <span className="text-base text-base-content/70">GBTUD</span>
            </div>
          </div>

          <div className="stat rounded-2xl bg-base-200/60">
            <div className="stat-title text-xs uppercase tracking-[0.2em]">
              Regalías acumuladas
            </div>
            <div className="stat-value text-primary text-lg">
              {regaliasAcumuladas / 1_000_000_000 > 1
                ? `${(regaliasAcumuladas / 1_000_000_000).toLocaleString('es-ES', {
                    maximumFractionDigits: 2,
                  })} B`
                : `${(regaliasAcumuladas / 1_000_000).toLocaleString('es-ES', {
                    maximumFractionDigits: 2,
                  })} M`}{' '}
              <span className="text-base text-base-content/70">COP</span>
            </div>
          </div>
        </div>
      </section>

      {analysis && (
        <section className="glass-panel p-6 space-y-3">
          <div className="space-y-1">
            <h3 className="text-xl font-semibold">Análisis generado con IA</h3>
            <p className="text-sm text-base-content/70">
              Interpretación automática a partir de los indicadores integrados de gas, electricidad y regalías.
            </p>
          </div>
          <div className="prose prose-sm max-w-none text-base-content/80 whitespace-pre-wrap">
            {analysis}
          </div>
        </section>
      )}

      <section className="glass-panel p-6 space-y-4">
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <h3 className="text-xl font-semibold">Reconciliación oferta vs demanda de gas</h3>
            <p className="text-sm text-base-content/70">
              Comparación anual entre la demanda proyectada UPME (ESC_MEDIO) y la oferta declarada de gas natural.
            </p>
          </div>
        </div>

        <div className="w-full h-[360px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={balanceOfertaDemanda}>
              <defs>
                <linearGradient id="colorDemanda" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.9} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.05} />
                </linearGradient>
                <linearGradient id="colorOferta" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#22c55e" stopOpacity={0.9} />
                  <stop offset="95%" stopColor="#22c55e" stopOpacity={0.05} />
                </linearGradient>
                <linearGradient id="colorBrecha" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f97316" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#f97316" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" />
              <YAxis
                label={{
                  value: 'GBTUD',
                  angle: -90,
                  position: 'insideLeft',
                }}
              />
              <Tooltip
                formatter={(value: number, name) => {
                  const formatted = value.toLocaleString('es-ES', {
                    maximumFractionDigits: 0,
                  })
                  if (name === 'brecha') {
                    return [`${formatted} GBTUD`, 'Brecha (oferta - demanda)']
                  }
                  if (name === 'oferta_gas') {
                    return [`${formatted} GBTUD`, 'Oferta gas']
                  }
                  return [`${formatted} GBTUD`, 'Demanda gas']
                }}
                labelFormatter={(label) => `Año: ${label}`}
              />
              <Legend
                formatter={(value) => {
                  if (value === 'demanda_gas') return 'Demanda gas (UPME, ESC_MEDIO)'
                  if (value === 'oferta_gas') return 'Oferta gas (declaración)'
                  if (value === 'brecha') return 'Brecha (oferta - demanda)'
                  return value
                }}
              />
              <Area
                type="monotone"
                dataKey="demanda_gas"
                stroke="#3b82f6"
                fill="url(#colorDemanda)"
                name="demanda_gas"
              />
              <Area
                type="monotone"
                dataKey="oferta_gas"
                stroke="#22c55e"
                fill="url(#colorOferta)"
                name="oferta_gas"
              />
              <Line
                type="monotone"
                dataKey="brecha"
                stroke="#f97316"
                strokeWidth={2}
                name="brecha"
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="glass-panel p-6 space-y-4">
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <h3 className="text-xl font-semibold">Regalías anuales</h3>
            <p className="text-sm text-base-content/70">
              Evolución de las regalías totales y las asociadas a gas natural, agregadas por año.
            </p>
          </div>
        </div>

        <div className="w-full h-[320px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={regalíasPorAnio}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" />
              <YAxis
                label={{
                  value: 'COP (miles de millones)',
                  angle: -90,
                  position: 'insideLeft',
                }}
                tickFormatter={(v) =>
                  (v as number).toLocaleString('es-ES', { maximumFractionDigits: 0 })
                }
              />
              <Tooltip
                formatter={(value: number, name) => {
                  const billions = value / 1_000_000_000
                  const formatted = billions.toLocaleString('es-ES', {
                    maximumFractionDigits: 2,
                  })
                  if (name === 'gas') return [`${formatted} B COP`, 'Regalías gas']
                  return [`${formatted} B COP`, 'Regalías totales']
                }}
                labelFormatter={(label) => `Año: ${label}`}
              />
              <Legend
                formatter={(value) => {
                  if (value === 'total') return 'Regalías totales'
                  if (value === 'gas') return 'Regalías asociadas a gas'
                  return value
                }}
              />
              <Line
                type="monotone"
                dataKey="total"
                name="total"
                stroke="#6366f1"
                strokeWidth={2}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="gas"
                name="gas"
                stroke="#22c55e"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="glass-panel p-6 space-y-4">
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <h3 className="text-xl font-semibold">Resumen integrado por año</h3>
            <p className="text-sm text-base-content/70">
              Indicadores clave combinando demanda y oferta de gas, demanda eléctrica y regalías.
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="table table-zebra table-sm w-full">
            <thead>
              <tr>
                <th>Año</th>
                <th className="text-right">Demanda gas (GBTUD)</th>
                <th className="text-right">Oferta gas (GBTUD)</th>
                <th className="text-right">Brecha (GBTUD)</th>
                <th className="text-right">Demanda eléctrica (GWh)</th>
                <th className="text-right">Regalías (COP M)</th>
              </tr>
            </thead>
            <tbody>
              {tablaIntegrada.map((row) => (
                <tr key={row.year}>
                  <td>{row.year}</td>
                  <td className="text-right">
                    {row.demandaGas.toLocaleString('es-ES', { maximumFractionDigits: 0 })}
                  </td>
                  <td className="text-right">
                    {row.ofertaGas.toLocaleString('es-ES', { maximumFractionDigits: 0 })}
                  </td>
                  <td className="text-right">
                    {row.brecha.toLocaleString('es-ES', { maximumFractionDigits: 0 })}
                  </td>
                  <td className="text-right">
                    {row.demandaElec.toLocaleString('es-ES', { maximumFractionDigits: 0 })}
                  </td>
                  <td className="text-right">
                    {(row.regalias / 1_000_000).toLocaleString('es-ES', {
                      maximumFractionDigits: 1,
                    })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}


