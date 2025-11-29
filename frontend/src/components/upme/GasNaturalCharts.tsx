import { useEffect, useMemo, useState } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { loadGasNaturalPage } from '@/services/upmeData.service';
import type { GasNaturalRecord } from '@/types/upme.types';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const COLORS = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1'];

export function GasNaturalCharts() {
  const [selectedCategoria, setSelectedCategoria] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const pageSize = 20;
  const apiPageSize = 5000;

  const {
    data,
    isLoading,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery<GasNaturalRecord[]>({
    queryKey: ['gas-natural-paged'],
    queryFn: async ({ pageParam }) =>
      loadGasNaturalPage((pageParam as number) ?? 0, apiPageSize),
    getNextPageParam: (lastPage, allPages) =>
      lastPage.length === apiPageSize ? allPages.length : undefined,
    initialPageParam: 0,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  useEffect(() => {
    if (hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  const flatData: GasNaturalRecord[] = useMemo(
    () => ((data?.pages as GasNaturalRecord[][]) ?? []).flat(),
    [data]
  );

  // Obtener todas las categorías disponibles
  const categorias = useMemo(() => {
    if (!flatData.length) return [];
    return Array.from(new Set(flatData.map(d => d.categoria))).sort();
  }, [flatData]);

  // Datos por categoría y escenario
  const categoriaData = useMemo(() => {
    if (!flatData.length) return [];

    const filtered = selectedCategoria 
      ? flatData.filter(d => d.categoria === selectedCategoria)
      : flatData;

    const grouped = new Map<string, { year: string; ESC_BAJO?: number; ESC_MEDIO?: number; ESC_ALTO?: number }>();

    filtered.forEach(record => {
      if (record.periodicidad === 'mensual') {
        const year = record.period_key.split('-')[0];
        const key = year;
        
        if (!grouped.has(key)) {
          grouped.set(key, { year });
        }
        
        const entry = grouped.get(key)!;
        // Sumar valores mensuales para obtener total anual
        entry[record.escenario] = (entry[record.escenario] || 0) + record.valor;
      }
    });

    return Array.from(grouped.values())
      .sort((a, b) => parseInt(a.year) - parseInt(b.year))
      .map(entry => ({
        ...entry,
        ESC_BAJO: entry.ESC_BAJO || 0,
        ESC_MEDIO: entry.ESC_MEDIO || 0,
        ESC_ALTO: entry.ESC_ALTO || 0,
      }));
  }, [data, selectedCategoria]);

  // Distribución por categoría (último año, escenario medio)
  const categoriaDistribution = useMemo(() => {
    if (!flatData.length) return [];

    const lastYear = Math.max(...flatData.map(d => parseInt(d.period_key.split('-')[0])));
    const filtered = flatData.filter(
      d => d.period_key.startsWith(`${lastYear}-`) && 
           d.escenario === 'ESC_MEDIO' && 
           d.periodicidad === 'mensual'
    );

    const grouped = new Map<string, number>();
    filtered.forEach(record => {
      const current = grouped.get(record.categoria) || 0;
      grouped.set(record.categoria, current + record.valor);
    });

    return Array.from(grouped.entries())
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value);
  }, [data]);

  // Datos mensuales para la categoría seleccionada
  const monthlyData = useMemo(() => {
    if (!flatData.length || !selectedCategoria) return [];

    return flatData
      .filter(r => r.categoria === selectedCategoria && r.escenario === 'ESC_MEDIO' && r.periodicidad === 'mensual')
      .map(r => ({
        date: r.period_key,
        month: new Date(r.period_key).toLocaleDateString('es-ES', { month: 'short', year: 'numeric' }),
        valor: r.valor,
      }))
      .sort((a, b) => a.date.localeCompare(b.date))
      .slice(-24); // Últimos 24 meses
  }, [flatData, selectedCategoria]);

  // Tabla: búsqueda y paginación sobre todos los registros de demanda de gas
  const filteredData = useMemo(() => {
    if (!flatData.length) return [];
    const term = search.toLowerCase().trim();
    if (!term) return flatData;

    return flatData.filter((row) => {
      return (
        row.period_key.toLowerCase().includes(term) ||
        row.categoria.toLowerCase().includes(term) ||
        (row.region?.toLowerCase().includes(term) ?? false) ||
        (row.nodo?.toLowerCase().includes(term) ?? false) ||
        row.escenario.toLowerCase().includes(term) ||
        (row.revision?.toLowerCase().includes(term) ?? false)
      );
    });
  }, [flatData, search]);

  const totalPages = Math.max(1, Math.ceil(filteredData.length / pageSize));

  const paginatedData = useMemo(() => {
    const start = page * pageSize;
    return filteredData.slice(start, start + pageSize);
  }, [filteredData, page, pageSize]);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="glass-panel p-6 space-y-4 animate-pulse">
          <div className="h-6 w-56 rounded-xl bg-base-300" />
          <div className="h-72 rounded-3xl bg-base-300" />
        </div>
        <div className="glass-panel p-6 space-y-4 animate-pulse">
          <div className="h-6 w-64 rounded-xl bg-base-300" />
          <div className="h-72 rounded-3xl bg-base-300" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-error">
        <span>Error al cargar datos de gas natural</span>
      </div>
    );
  }

  if (!flatData.length) {
    return (
      <div className="alert alert-warning">
        <span>No hay datos disponibles</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Selector de categoría */}
      <div className="glass-panel p-4">
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setSelectedCategoria(null)}
            className={`btn btn-sm ${selectedCategoria === null ? 'btn-primary' : 'btn-outline'}`}
          >
            Todas
          </button>
          {categorias.map(cat => (
            <button
              key={cat}
              onClick={() => setSelectedCategoria(cat)}
              className={`btn btn-sm ${selectedCategoria === cat ? 'btn-primary' : 'btn-outline'}`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      <div className="glass-panel p-6">
        <h3 className="text-xl font-semibold mb-4">
          Demanda de Gas Natural {selectedCategoria ? `- ${selectedCategoria}` : 'por Escenario'}
        </h3>
        <p className="text-sm text-base-content/70 mb-4">
          Demanda proyectada en GBTUD
        </p>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={categoriaData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" />
            <YAxis label={{ value: 'GBTUD', angle: -90, position: 'insideLeft' }} />
            <Tooltip formatter={(value: number) => `${value.toLocaleString('es-ES', { maximumFractionDigits: 2 })} GBTUD`} />
            <Legend />
            <Line type="monotone" dataKey="ESC_BAJO" stroke="#ef4444" strokeWidth={2} name="Escenario Bajo" />
            <Line type="monotone" dataKey="ESC_MEDIO" stroke="#3b82f6" strokeWidth={2} name="Escenario Medio" />
            <Line type="monotone" dataKey="ESC_ALTO" stroke="#10b981" strokeWidth={2} name="Escenario Alto" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {selectedCategoria && monthlyData.length > 0 && (
        <div className="glass-panel p-6">
          <h3 className="text-xl font-semibold mb-4">Tendencia Mensual - {selectedCategoria}</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={monthlyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" angle={-45} textAnchor="end" height={80} />
              <YAxis label={{ value: 'GBTUD', angle: -90, position: 'insideLeft' }} />
              <Tooltip formatter={(value: number) => `${value.toLocaleString('es-ES', { maximumFractionDigits: 2 })} GBTUD`} />
              <Line type="monotone" dataKey="valor" stroke="#3b82f6" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-panel p-6">
          <h3 className="text-xl font-semibold mb-4">Distribución por Categoría (Último Año - Escenario Medio)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={categoriaDistribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${((percent ?? 0) * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {categoriaDistribution.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value: number) => `${value.toLocaleString('es-ES', { maximumFractionDigits: 2 })} GBTUD`} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="stats stats-vertical shadow">
          <div className="stat">
            <div className="stat-title">Total Registros</div>
            <div className="stat-value text-primary">{flatData.length.toLocaleString()}</div>
          </div>
          <div className="stat">
            <div className="stat-title">Categorías</div>
            <div className="stat-value text-secondary">{categorias.length}</div>
          </div>
          <div className="stat">
            <div className="stat-title">Demanda Total Promedio</div>
            <div className="stat-value text-accent">
              {flatData.length > 0
                ? `${Math.round(
                    flatData.reduce(
                      (sum: number, d: GasNaturalRecord) => sum + d.valor,
                      0
                    ) / flatData.length
                  ).toLocaleString()} GBTUD`
                : '0 GBTUD'}
            </div>
          </div>
        </div>
      </div>

      {/* Tabla detallada de registros */}
      <div className="glass-panel p-6 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <h3 className="text-lg font-semibold">Registros detallados</h3>
          <div className="form-control w-full md:w-64">
            <input
              type="text"
              placeholder="Buscar por fecha, categoría, región, nodo, escenario..."
              className="input input-bordered input-sm w-full"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(0);
              }}
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="table table-zebra table-sm w-full">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Categoría</th>
                <th>Región</th>
                <th>Nodo</th>
                <th>Escenario</th>
                <th className="text-right">Valor (GBTUD)</th>
              </tr>
            </thead>
            <tbody>
              {paginatedData.map((row, idx) => (
                <tr key={`${row.period_key}-${row.categoria}-${row.escenario}-${idx}`}>
                  <td>{row.period_key}</td>
                  <td>{row.categoria}</td>
                  <td>{row.region ?? '-'}</td>
                  <td>{row.nodo ?? '-'}</td>
                  <td>{row.escenario}</td>
                  <td className="text-right">
                    {row.valor.toLocaleString('es-ES', { maximumFractionDigits: 2 })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between text-sm mt-2">
          <span>
            Mostrando{' '}
            {filteredData.length === 0
              ? 0
              : `${page * pageSize + 1}-${Math.min((page + 1) * pageSize, filteredData.length)}`}{' '}
            de {filteredData.length.toLocaleString()} registros
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
  );
}

