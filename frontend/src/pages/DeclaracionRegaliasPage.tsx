import { useEffect, useMemo, useState } from 'react'
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
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import { loadOfertaGasPage, loadRegaliasPage } from '@/services/declaracionRegaliasData.service'
import type { OfertaGasRecord, RegaliasRecord } from '@/types/declaracion_regalias.types'

export function DeclaracionGasPage() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(0)
  const pageSize = 20
  const apiPageSize = 5000

  const {
    data,
    isLoading,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery<OfertaGasRecord[]>({
    queryKey: ['oferta-gas-paged'],
    queryFn: async ({ pageParam }) =>
      loadOfertaGasPage((pageParam as number) ?? 0, apiPageSize),
    getNextPageParam: (lastPage, allPages) =>
      lastPage.length === apiPageSize ? allPages.length : undefined,
    initialPageParam: 0,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  })

  // Ir trayendo páginas adicionales automáticamente para que el dashboard se complete solo
  useEffect(() => {
    if (hasNextPage && !isFetchingNextPage) {
      fetchNextPage()
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage])

  const flatData: OfertaGasRecord[] = useMemo(
    () => ((data?.pages as OfertaGasRecord[][]) ?? []).flat(),
    [data]
  )

  // Serie anual de volumen declarado
  const yearlySeries = useMemo(() => {
    if (!flatData.length) return []
    const byYear = new Map<string, number>()

    for (const row of flatData) {
      if (!row.period_key) continue
      const year = row.period_key.split('-')[0]
      const prev = byYear.get(year) ?? 0
      byYear.set(year, prev + (row.valor_gbtud || 0))
    }

    return Array.from(byYear.entries())
      .map(([year, total]) => ({ year, total }))
      .sort((a, b) => Number(a.year) - Number(b.year))
  }, [flatData])

  // Top operadores por volumen total
  const topOperadores = useMemo(() => {
    if (!flatData.length) return []
    const byOp = new Map<string, number>()

    for (const row of flatData) {
      const key = row.operador || 'N/D'
      const prev = byOp.get(key) ?? 0
      byOp.set(key, prev + (row.valor_gbtud || 0))
    }

    return Array.from(byOp.entries())
      .map(([operador, total]) => ({ operador, total }))
      .sort((a, b) => b.total - a.total)
      .slice(0, 10)
  }, [data])

  const filtered = useMemo(() => {
    if (!flatData.length) return []
    const term = search.toLowerCase().trim()
    if (!term) return flatData

    return flatData.filter((row) => {
      return (
        row.period_key.toLowerCase().includes(term) ||
        row.operador.toLowerCase().includes(term) ||
        (row.tipo_produccion ?? '').toLowerCase().includes(term) ||
        (row.source_id ?? '').toLowerCase().includes(term)
      )
    })
  }, [flatData, search])

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize))

  const paginated = useMemo(() => {
    const start = page * pageSize
    return filtered.slice(start, start + pageSize)
  }, [filtered, page, pageSize])

  const totalDeclarado = useMemo(
    () => flatData.reduce((sum, r) => sum + (r.valor_gbtud || 0), 0),
    [flatData]
  )

  const operadoresUnicos = useMemo(
    () => new Set(flatData.map((r) => r.operador)).size,
    [flatData]
  )

  if (isLoading) {
    return (
      <div className="space-y-6">
        <section className="space-y-2">
          <p className="text-sm uppercase tracking-[0.2em] text-base-content/50">Hechos</p>
          <h2 className="text-gradient text-3xl font-semibold">Declaración de Gas Natural</h2>
          <p className="text-base text-base-content/70">
            Cargando series de declaración de gas natural. Esto puede tomar unos segundos...
          </p>
        </section>

        <div className="glass-panel p-6 space-y-4 animate-pulse">
          <div className="h-6 w-48 rounded-xl bg-base-300" />
          <div className="h-72 rounded-3xl bg-base-300" />
        </div>

        <div className="glass-panel p-6 space-y-4 animate-pulse">
          <div className="h-6 w-64 rounded-xl bg-base-300" />
          <div className="h-72 rounded-3xl bg-base-300" />
        </div>

        <div className="stats stats-vertical lg:stats-horizontal shadow w-full animate-pulse">
          <div className="stat">
            <div className="stat-title">Total registros</div>
            <div className="stat-value bg-base-300 rounded-xl h-8 w-24" />
          </div>
          <div className="stat">
            <div className="stat-title">Operadores</div>
            <div className="stat-value bg-base-300 rounded-xl h-8 w-24" />
          </div>
          <div className="stat">
            <div className="stat-title">Volumen declarado (suma)</div>
            <div className="stat-value bg-base-300 rounded-xl h-8 w-40" />
          </div>
        </div>

        <div className="glass-panel p-6 space-y-4 animate-pulse">
          <div className="h-6 w-72 rounded-xl bg-base-300" />
          <div className="h-40 rounded-3xl bg-base-300" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="alert alert-error">
        <span>Error al cargar datos de declaración de gas</span>
      </div>
    )
  }

  if (!flatData.length && !isLoading) {
    return (
      <div className="alert alert-warning">
        <span>No hay datos de fact_oferta_gas disponibles</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <section className="space-y-2">
        <p className="text-sm uppercase tracking-[0.2em] text-base-content/50">Hechos</p>
        <h2 className="text-gradient text-3xl font-semibold">Declaración de Gas Natural</h2>
        <p className="text-base text-base-content/70">
          Declaración de producción de gas natural por operador (fuente MinMinas).
        </p>
      </section>

      {/* Gráfica de serie anual de volumen declarado */}
      <div className="glass-panel p-6 space-y-4">
        <h3 className="text-lg font-semibold">Volumen declarado anual</h3>
        <p className="text-sm text-base-content/60">Suma de volumen declarado por año (GBTUD).</p>
        <div style={{ height: 320 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={yearlySeries}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" />
              <YAxis />
              <Tooltip
                formatter={(value: number) =>
                  `${value.toLocaleString('es-ES', { maximumFractionDigits: 2 })} GBTUD`
                }
              />
              <Legend />
              <Line type="monotone" dataKey="total" name="Volumen declarado" stroke="#3b82f6" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top operadores por volumen */}
      <div className="glass-panel p-6 space-y-4">
        <h3 className="text-lg font-semibold">Top operadores por volumen declarado</h3>
        <p className="text-sm text-base-content/60">Suma total de volumen declarado por operador.</p>
        <div style={{ height: 360 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={topOperadores} layout="vertical" margin={{ left: 80 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis type="category" dataKey="operador" />
              <Tooltip
                formatter={(value: number) =>
                  `${value.toLocaleString('es-ES', { maximumFractionDigits: 2 })} GBTUD`
                }
              />
              <Legend />
              <Bar dataKey="total" name="Volumen declarado" fill="#10b981" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Gráfica de serie anual de valor de regalías */}
      <div className="glass-panel p-6 space-y-4">
        <h3 className="text-lg font-semibold">Valor de regalías anual</h3>
        <p className="text-sm text-base-content/60">Suma de valor de regalías por año (COP).</p>
        <div style={{ height: 320 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={yearlySeries}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" />
              <YAxis />
              <Tooltip
                formatter={(value: number) =>
                  `${value.toLocaleString('es-ES', { maximumFractionDigits: 0 })} COP`
                }
              />
              <Legend />
              <Line type="monotone" dataKey="total" name="Valor regalías" stroke="#f97316" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="stats stats-vertical lg:stats-horizontal shadow w-full">
        <div className="stat">
          <div className="stat-title">Total registros</div>
          <div className="stat-value text-primary">{flatData.length.toLocaleString()}</div>
        </div>
        <div className="stat">
          <div className="stat-title">Operadores</div>
          <div className="stat-value text-secondary">{operadoresUnicos.toLocaleString()}</div>
        </div>
        <div className="stat">
          <div className="stat-title">Volumen declarado (suma)</div>
          <div className="stat-value text-accent">
            {Math.round(totalDeclarado).toLocaleString('es-ES')} GBTUD
          </div>
        </div>
      </div>

      <div className="glass-panel p-6 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div>
            <h3 className="text-lg font-semibold">Declaración de producción de gas natural</h3>
            <p className="text-sm text-base-content/60">
              Filtra por fecha, operador o tipo de producción.
            </p>
          </div>
          <div className="form-control w-full md:w-72">
            <input
              type="text"
              placeholder="Buscar por fecha, operador, tipo..."
              className="input input-bordered input-sm w-full"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value)
                setPage(0)
              }}
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="table table-zebra table-sm w-full">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Operador</th>
                <th>Tipo producción</th>
                <th className="text-right">Volumen (GBTUD)</th>
              </tr>
            </thead>
            <tbody>
              {paginated.map((row: OfertaGasRecord) => (
                <tr key={row.id}>
                  <td>{row.period_key}</td>
                  <td>{row.operador}</td>
                  <td>{row.tipo_produccion ?? '-'}</td>
                  <td className="text-right">
                    {row.valor_gbtud.toLocaleString('es-ES', { maximumFractionDigits: 2 })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between text-sm mt-2">
          <span>
            Mostrando{' '}
            {filtered.length === 0
              ? 0
              : `${page * pageSize + 1}-${Math.min((page + 1) * pageSize, filtered.length)}`}{' '}
            de {filtered.length.toLocaleString()} registros
          </span>
          <div className="join">
            <button
              className="btn btn-xs join-item"
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
            >
              «
            </button>
            <button className="btn btn-xs join-item" disabled>
              Página {page + 1} de {totalPages}
            </button>
            <button
              className="btn btn-xs join-item"
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
            >
              »
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export function RegaliasPage() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(0)
  const pageSize = 20
  const apiPageSize = 5000

  const {
    data,
    isLoading,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery<RegaliasRecord[]>({
    queryKey: ['regalias-paged'],
    queryFn: async ({ pageParam }) =>
      loadRegaliasPage((pageParam as number) ?? 0, apiPageSize),
    getNextPageParam: (lastPage, allPages) =>
      lastPage.length === apiPageSize ? allPages.length : undefined,
    initialPageParam: 0,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  })

  useEffect(() => {
    if (hasNextPage && !isFetchingNextPage) {
      fetchNextPage()
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage])

  const flatData: RegaliasRecord[] = useMemo(
    () => ((data?.pages as RegaliasRecord[][]) ?? []).flat(),
    [data]
  )

  // Serie anual de valor de regalías
  const yearlySeries = useMemo(() => {
    if (!flatData.length) return []
    const byYear = new Map<string, number>()

    for (const row of flatData) {
      if (!row.period_key) continue
      const year = row.period_key.split('-')[0]
      const prev = byYear.get(year) ?? 0
      byYear.set(year, prev + (row.valor_regalias_cop || 0))
    }

    return Array.from(byYear.entries())
      .map(([year, total]) => ({ year, total }))
      .sort((a, b) => Number(a.year) - Number(b.year))
  }, [data])

  // Distribución por tipo de hidrocarburo
  const byHidrocarburo = useMemo(() => {
    if (!flatData.length) return []
    const byType = new Map<string, number>()

    for (const row of flatData) {
      const key = row.tipo_hidrocarburo || 'N/D'
      const prev = byType.get(key) ?? 0
      byType.set(key, prev + (row.valor_regalias_cop || 0))
    }

    return Array.from(byType.entries())
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value)
  }, [flatData])

  const pieColors = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16']

  const filtered = useMemo(() => {
    if (!flatData.length) return []
    const term = search.toLowerCase().trim()
    if (!term) return flatData

    return flatData.filter((row) => {
      return (
        row.period_key.toLowerCase().includes(term) ||
        (row.tipo_produccion ?? '').toLowerCase().includes(term) ||
        (row.tipo_hidrocarburo ?? '').toLowerCase().includes(term) ||
        (row.regimen_regalias ?? '').toLowerCase().includes(term)
      )
    })
  }, [flatData, search])

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize))

  const paginated = useMemo(() => {
    const start = page * pageSize
    return filtered.slice(start, start + pageSize)
  }, [filtered, page, pageSize])

  const totalRegalias = useMemo(
    () => flatData.reduce((sum, r) => sum + (r.valor_regalias_cop || 0), 0),
    [flatData]
  )

  const totalVolumen = useMemo(
    () => flatData.reduce((sum, r) => sum + (r.volumen_regalia || 0), 0),
    [flatData]
  )

  if (isLoading) {
    return (
      <div className="space-y-6">
        <section className="space-y-2">
          <p className="text-sm uppercase tracking-[0.2em] text-base-content/50">Hechos</p>
          <h2 className="text-gradient text-3xl font-semibold">Regalías por Campo</h2>
          <p className="text-base text-base-content/70">
            Cargando series históricas de regalías. Esto puede tomar unos segundos...
          </p>
        </section>

        <div className="glass-panel p-6 space-y-4 animate-pulse">
          <div className="h-6 w-56 rounded-xl bg-base-300" />
          <div className="h-72 rounded-3xl bg-base-300" />
        </div>

        <div className="glass-panel p-6 space-y-4 animate-pulse">
          <div className="h-6 w-72 rounded-xl bg-base-300" />
          <div className="h-72 rounded-3xl bg-base-300" />
        </div>

        <div className="stats stats-vertical lg:stats-horizontal shadow w-full animate-pulse">
          <div className="stat">
            <div className="stat-title">Total registros</div>
            <div className="stat-value bg-base-300 rounded-xl h-8 w-24" />
          </div>
          <div className="stat">
            <div className="stat-title">Valor regalías (suma)</div>
            <div className="stat-value bg-base-300 rounded-xl h-8 w-40" />
          </div>
          <div className="stat">
            <div className="stat-title">Volumen regalía (suma)</div>
            <div className="stat-value bg-base-300 rounded-xl h-8 w-40" />
          </div>
        </div>

        <div className="glass-panel p-6 space-y-4 animate-pulse">
          <div className="h-6 w-80 rounded-xl bg-base-300" />
          <div className="h-40 rounded-3xl bg-base-300" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="alert alert-error">
        <span>Error al cargar datos de regalías</span>
      </div>
    )
  }

  if (!flatData.length && !isLoading) {
    return (
      <div className="alert alert-warning">
        <span>No hay datos de fact_regalias disponibles</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <section className="space-y-2">
        <p className="text-sm uppercase tracking-[0.2em] text-base-content/50">Hechos</p>
        <h2 className="text-gradient text-3xl font-semibold">Regalías por Campo</h2>
        <p className="text-base text-base-content/70">
          Liquidación de regalías por campo y tipo de hidrocarburo (fuente ANH).
        </p>
      </section>

      {/* Gráfica de serie anual de valor de regalías */}
      <div className="glass-panel p-6 space-y-4">
        <h3 className="text-lg font-semibold">Valor de regalías anual</h3>
        <p className="text-sm text-base-content/60">Suma de valor de regalías por año (COP).</p>
        <div style={{ height: 320 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={yearlySeries}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" />
              <YAxis />
              <Tooltip
                formatter={(value: number) =>
                  `${value.toLocaleString('es-ES', { maximumFractionDigits: 0 })} COP`
                }
              />
              <Legend />
              <Line type="monotone" dataKey="total" name="Valor regalías" stroke="#f97316" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Distribución por tipo de hidrocarburo */}
      <div className="glass-panel p-6 space-y-4">
        <h3 className="text-lg font-semibold">Distribución por tipo de hidrocarburo</h3>
        <p className="text-sm text-base-content/60">Participación de cada tipo en el valor total de regalías.</p>
        <div style={{ height: 320 }}>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={byHidrocarburo}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={({ name, percent }: { name?: string; percent?: number }) =>
                  `${name ?? 'N/D'}: ${(((percent ?? 0) * 100).toFixed(0))}%`
                }
              >
                {byHidrocarburo.map((item, idx) => (
                  <Cell key={item.name} fill={pieColors[idx % pieColors.length]} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value: number) =>
                  `${value.toLocaleString('es-ES', { maximumFractionDigits: 0 })} COP`
                }
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="stats stats-vertical lg:stats-horizontal shadow w-full">
        <div className="stat">
          <div className="stat-title">Total registros</div>
          <div className="stat-value text-primary">{flatData.length.toLocaleString()}</div>
        </div>
        <div className="stat">
          <div className="stat-title">Valor regalías (suma)</div>
          <div className="stat-value text-secondary">
            {Math.round(totalRegalias).toLocaleString('es-ES')} COP
          </div>
        </div>
        <div className="stat">
          <div className="stat-title">Volumen regalía (suma)</div>
          <div className="stat-value text-accent">
            {Math.round(totalVolumen).toLocaleString('es-ES')} {flatData[0]?.unidad ?? ''}
          </div>
        </div>
      </div>

      <div className="glass-panel p-6 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div>
            <h3 className="text-lg font-semibold">Liquidación de regalías por campo</h3>
            <p className="text-sm text-base-content/60">
              Filtra por fecha, tipo de producción, hidrocarburo o régimen.
            </p>
          </div>
          <div className="form-control w-full md:w-72">
            <input
              type="text"
              placeholder="Buscar por fecha, tipo, régimen..."
              className="input input-bordered input-sm w-full"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value)
                setPage(0)
              }}
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="table table-zebra table-sm w-full">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Tipo producción</th>
                <th>Hidrocarburo</th>
                <th>Régimen</th>
                <th className="text-right">Valor regalías (COP)</th>
              </tr>
            </thead>
            <tbody>
              {paginated.map((row: RegaliasRecord) => (
                <tr key={row.id}>
                  <td>{row.period_key}</td>
                  <td>{row.tipo_produccion ?? '-'}</td>
                  <td>{row.tipo_hidrocarburo ?? '-'}</td>
                  <td>{row.regimen_regalias ?? '-'}</td>
                  <td className="text-right">
                    {(row.valor_regalias_cop || 0).toLocaleString('es-ES', { maximumFractionDigits: 2 })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between text-sm mt-2">
          <span>
            Mostrando{' '}
            {filtered.length === 0
              ? 0
              : `${page * pageSize + 1}-${Math.min((page + 1) * pageSize, filtered.length)}`}{' '}
            de {filtered.length.toLocaleString()} registros
          </span>
          <div className="join">
            <button
              className="btn btn-xs join-item"
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
            >
              «
            </button>
            <button className="btn btn-xs join-item" disabled>
              Página {page + 1} de {totalPages}
            </button>
            <button
              className="btn btn-xs join-item"
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
            >
              »
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
