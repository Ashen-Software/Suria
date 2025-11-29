import { useEffect, useMemo, useState } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { loadPotenciaMaximaPage } from '@/services/upmeData.service';
import type { PotenciaMaximaRecord } from '@/types/upme.types';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts';

export function PotenciaMaximaCharts() {
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
  } = useInfiniteQuery<PotenciaMaximaRecord[]>({
    queryKey: ['potencia-maxima-paged'],
    queryFn: async ({ pageParam }) =>
      loadPotenciaMaximaPage((pageParam as number) ?? 0, apiPageSize),
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

  const flatData: PotenciaMaximaRecord[] = useMemo(
    () => ((data?.pages as PotenciaMaximaRecord[][]) ?? []).flat(),
    [data]
  );

  const chartData = useMemo(() => {
    if (!flatData.length) return [];

    // Verificar qué escenarios realmente existen en los datos
    const availableScenarios = new Set(flatData.map(r => r.escenario));
    
    const grouped = new Map<string, { year: string; ESC_BAJO: number[]; ESC_MEDIO: number[]; ESC_ALTO: number[] }>();

    flatData.forEach(record => {
      if (record.periodicidad === 'mensual') {
        const year = record.period_key.split('-')[0];
        const key = year;
        
        if (!grouped.has(key)) {
          grouped.set(key, { year, ESC_BAJO: [], ESC_MEDIO: [], ESC_ALTO: [] });
        }
        
        const entry = grouped.get(key)!;
        entry[record.escenario].push(record.valor);
      }
    });

    return Array.from(grouped.values())
      .sort((a, b) => parseInt(a.year) - parseInt(b.year))
      .map(entry => {
        const result: any = { year: entry.year };
        // Solo incluir escenarios que realmente existen en los datos
        if (availableScenarios.has('ESC_BAJO') && entry.ESC_BAJO.length > 0) {
          result.ESC_BAJO = entry.ESC_BAJO.reduce((a, b) => a + b, 0) / entry.ESC_BAJO.length;
        }
        if (availableScenarios.has('ESC_MEDIO') && entry.ESC_MEDIO.length > 0) {
          result.ESC_MEDIO = entry.ESC_MEDIO.reduce((a, b) => a + b, 0) / entry.ESC_MEDIO.length;
        }
        if (availableScenarios.has('ESC_ALTO') && entry.ESC_ALTO.length > 0) {
          result.ESC_ALTO = entry.ESC_ALTO.reduce((a, b) => a + b, 0) / entry.ESC_ALTO.length;
        }
        return result;
      });
  }, [flatData]);

  // Determinar qué escenarios tienen datos para renderizar
  const hasEscenarioBajo = useMemo(() => {
    return chartData.some(d => d.ESC_BAJO !== null && d.ESC_BAJO !== undefined && d.ESC_BAJO > 0);
  }, [chartData]);

  const hasEscenarioMedio = useMemo(() => {
    return chartData.some(d => d.ESC_MEDIO !== null && d.ESC_MEDIO !== undefined && d.ESC_MEDIO > 0);
  }, [chartData]);

  const hasEscenarioAlto = useMemo(() => {
    return chartData.some(d => d.ESC_ALTO !== null && d.ESC_ALTO !== undefined && d.ESC_ALTO > 0);
  }, [chartData]);

  // Datos mensuales detallados
  const monthlyData = useMemo(() => {
    if (!flatData.length) return [];

    return flatData
      .filter(r => r.periodicidad === 'mensual' && r.escenario === 'ESC_MEDIO')
      .map(r => ({
        date: r.period_key,
        month: new Date(r.period_key).toLocaleDateString('es-ES', { month: 'short', year: 'numeric' }),
        valor: r.valor,
      }))
      .sort((a, b) => a.date.localeCompare(b.date))
      .slice(-36); // Últimos 36 meses
  }, [flatData]);

  // Tabla: búsqueda y paginación sobre todos los registros
  const filteredData = useMemo(() => {
    if (!flatData.length) return [];
    const term = search.toLowerCase().trim();
    if (!term) return flatData;

    return flatData.filter((row) => {
      return (
        row.period_key.toLowerCase().includes(term) ||
        row.periodicidad.toLowerCase().includes(term) ||
        row.escenario.toLowerCase().includes(term) ||
        row.unidad.toLowerCase().includes(term) ||
        (row.descriptor?.toLowerCase().includes(term) ?? false) ||
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
          <div className="h-6 w-72 rounded-xl bg-base-300" />
          <div className="h-72 rounded-3xl bg-base-300" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-error">
        <span>Error al cargar datos de potencia máxima</span>
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
      <div className="glass-panel p-6">
        <h3 className="text-xl font-semibold mb-4">Proyección de Potencia Máxima por Escenario</h3>
        <p className="text-sm text-base-content/70 mb-4">
          Potencia máxima proyectada en MW-mes
        </p>
        <ResponsiveContainer width="100%" height={400}>
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="colorBajo" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorMedio" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorAlto" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
                <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" />
            <YAxis label={{ value: 'MW-mes', angle: -90, position: 'insideLeft' }} />
            <Tooltip 
              formatter={(value: any) => {
                if (value === null || value === undefined) return 'N/A';
                const numValue = typeof value === 'number' ? value : parseFloat(value);
                if (isNaN(numValue)) return 'N/A';
                return `${numValue.toLocaleString('es-ES', { maximumFractionDigits: 0 })} MW`;
              }}
              labelFormatter={(label) => `Año: ${label}`}
            />
            <Legend />
            {hasEscenarioBajo && (
              <Area type="monotone" dataKey="ESC_BAJO" stackId="1" stroke="#ef4444" fill="url(#colorBajo)" name="Escenario Bajo" connectNulls={false} />
            )}
            {hasEscenarioMedio && (
              <Area type="monotone" dataKey="ESC_MEDIO" stackId="1" stroke="#3b82f6" fill="url(#colorMedio)" name="Escenario Medio" connectNulls={false} />
            )}
            {hasEscenarioAlto && (
              <Area type="monotone" dataKey="ESC_ALTO" stackId="1" stroke="#10b981" fill="url(#colorAlto)" name="Escenario Alto" connectNulls={false} />
            )}
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="glass-panel p-6">
        <h3 className="text-xl font-semibold mb-4">Tendencia Mensual (Últimos 36 meses - Escenario Medio)</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={monthlyData} margin={{ top: 5, right: 30, left: 20, bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="month" 
              angle={-45} 
              textAnchor="end" 
              height={80}
              interval="preserveStartEnd"
            />
            <YAxis label={{ value: 'MW', angle: -90, position: 'insideLeft' }} />
            <Tooltip 
              formatter={(value: number) => `${value.toLocaleString('es-ES', { maximumFractionDigits: 0 })} MW`}
              labelFormatter={(label) => `Período: ${label}`}
              contentStyle={{ backgroundColor: 'rgba(0, 0, 0, 0.8)', border: '1px solid #ccc', borderRadius: '4px' }}
            />
            <Line 
              type="monotone" 
              dataKey="valor" 
              stroke="#3b82f6" 
              strokeWidth={2} 
              dot={false}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="stats stats-vertical lg:stats-horizontal shadow w-full">
        <div className="stat">
          <div className="stat-title">Total Registros</div>
          <div className="stat-value text-primary">{flatData.length.toLocaleString()}</div>
        </div>
        <div className="stat">
          <div className="stat-title">Potencia Máxima Promedio</div>
          <div className="stat-value text-secondary">
            {Math.round(flatData.reduce((sum, d) => sum + d.valor, 0) / flatData.length).toLocaleString()} MW
          </div>
        </div>
        <div className="stat">
          <div className="stat-title">Período</div>
          <div className="stat-value text-accent">
            {new Set(flatData.map(d => d.year_span)).size}
          </div>
          <div className="stat-desc">Rangos de años</div>
        </div>
      </div>

      {/* Tabla detallada de registros */}
      <div className="glass-panel p-6 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <h3 className="text-lg font-semibold">Registros detallados</h3>
          <div className="form-control w-full md:w-64">
            <input
              type="text"
              placeholder="Buscar por fecha, escenario, unidad, revisión..."
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
                <th>Periodicidad</th>
                <th>Escenario</th>
                <th>Unidad</th>
                <th className="text-right">Valor</th>
                <th>Revisión</th>
              </tr>
            </thead>
            <tbody>
              {paginatedData.map((row, idx) => (
                <tr key={`${row.period_key}-${row.escenario}-${idx}`}>
                  <td>{row.period_key}</td>
                  <td className="capitalize">{row.periodicidad}</td>
                  <td>{row.escenario}</td>
                  <td>{row.unidad}</td>
                  <td className="text-right">
                    {row.valor.toLocaleString('es-ES', { maximumFractionDigits: 2 })}
                  </td>
                  <td>{row.revision}</td>
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

