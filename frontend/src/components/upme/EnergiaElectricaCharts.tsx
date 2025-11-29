import { useQuery } from '@tanstack/react-query';
import { loadEnergiaElectricaData } from '@/services/upmeData.service';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { useMemo, useState } from 'react';

export function EnergiaElectricaCharts() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['energia-electrica'],
    queryFn: loadEnergiaElectricaData,
    // Evitar refetch constante y reutilizar resultados
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });

  // Procesar datos para gráficos
  const chartData = useMemo(() => {
    if (!data) return [];

    // Verificar qué escenarios realmente existen en los datos
    const availableScenarios = new Set(data.map(r => r.escenario));
    
    // Agrupar por año y escenario, sumando valores anuales
    const grouped = new Map<string, { year: string; ESC_BAJO?: number; ESC_MEDIO?: number; ESC_ALTO?: number }>();

    data.forEach(record => {
      if (record.periodicidad === 'anual') {
        const year = record.period_key.split('-')[0];
        const key = year;
        
        if (!grouped.has(key)) {
          grouped.set(key, { year });
        }
        
        const entry = grouped.get(key)!;
        entry[record.escenario] = (entry[record.escenario] || 0) + record.valor;
      }
    });

    return Array.from(grouped.values())
      .sort((a, b) => parseInt(a.year) - parseInt(b.year))
      .map(entry => {
        const result: any = { year: entry.year };
        // Solo incluir escenarios que realmente existen en los datos
        if (availableScenarios.has('ESC_BAJO') && entry.ESC_BAJO) {
          result.ESC_BAJO = entry.ESC_BAJO;
        }
        if (availableScenarios.has('ESC_MEDIO') && entry.ESC_MEDIO) {
          result.ESC_MEDIO = entry.ESC_MEDIO;
        }
        if (availableScenarios.has('ESC_ALTO') && entry.ESC_ALTO) {
          result.ESC_ALTO = entry.ESC_ALTO;
        }
        return result;
      });
  }, [data]);

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

  // Datos mensuales para el último año disponible
  const monthlyData = useMemo(() => {
    if (!data) return [];

    const monthly = data
      .filter(r => r.periodicidad === 'mensual' && r.escenario === 'ESC_MEDIO')
      .map(r => ({
        date: r.period_key,
        month: new Date(r.period_key).toLocaleDateString('es-ES', { month: 'short', year: 'numeric' }),
        valor: r.valor,
      }))
      .sort((a, b) => a.date.localeCompare(b.date))
      .slice(-24); // Últimos 24 meses

    return monthly;
  }, [data]);

  // Tabla: búsqueda y paginación sobre todos los registros
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);
  const pageSize = 20;

  const filteredData = useMemo(() => {
    if (!data) return [];
    const term = search.toLowerCase().trim();
    if (!term) return data;

    return data.filter((row) => {
      return (
        row.period_key.toLowerCase().includes(term) ||
        row.periodicidad.toLowerCase().includes(term) ||
        row.escenario.toLowerCase().includes(term) ||
        row.unidad.toLowerCase().includes(term) ||
        (row.descriptor?.toLowerCase().includes(term) ?? false) ||
        (row.revision?.toLowerCase().includes(term) ?? false)
      );
    });
  }, [data, search]);

  const totalPages = Math.max(1, Math.ceil(filteredData.length / pageSize));

  const paginatedData = useMemo(() => {
    const start = page * pageSize;
    return filteredData.slice(start, start + pageSize);
  }, [filteredData, page, pageSize]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <span className="loading loading-spinner loading-lg"></span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-error">
        <span>Error al cargar datos de energía eléctrica</span>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="alert alert-warning">
        <span>No hay datos disponibles</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="glass-panel p-6">
        <h3 className="text-xl font-semibold mb-4">Proyección Anual de Energía Eléctrica por Escenario</h3>
        <p className="text-sm text-base-content/70 mb-4">
          Demanda proyectada en GWh-año para diferentes escenarios
        </p>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" />
            <YAxis label={{ value: 'GWh-año', angle: -90, position: 'insideLeft' }} />
            <Tooltip 
              formatter={(value: any) => {
                if (value === null || value === undefined) return 'N/A';
                const numValue = typeof value === 'number' ? value : parseFloat(value);
                if (isNaN(numValue)) return 'N/A';
                return `${numValue.toLocaleString('es-ES', { maximumFractionDigits: 0 })} GWh`;
              }}
              labelFormatter={(label) => `Año: ${label}`}
            />
            <Legend />
            {hasEscenarioBajo && (
              <Line type="monotone" dataKey="ESC_BAJO" stroke="#ef4444" strokeWidth={2} name="Escenario Bajo" connectNulls={false} />
            )}
            {hasEscenarioMedio && (
              <Line type="monotone" dataKey="ESC_MEDIO" stroke="#3b82f6" strokeWidth={2} name="Escenario Medio" connectNulls={false} />
            )}
            {hasEscenarioAlto && (
              <Line type="monotone" dataKey="ESC_ALTO" stroke="#10b981" strokeWidth={2} name="Escenario Alto" connectNulls={false} />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="glass-panel p-6">
        <h3 className="text-xl font-semibold mb-4">Tendencia Mensual (Últimos 24 meses - Escenario Medio)</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={monthlyData} margin={{ top: 5, right: 30, left: 20, bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="month" 
              angle={-45} 
              textAnchor="end" 
              height={80}
              interval="preserveStartEnd"
            />
            <YAxis label={{ value: 'GWh', angle: -90, position: 'insideLeft' }} />
            <Tooltip 
              formatter={(value: number) => `${value.toLocaleString('es-ES', { maximumFractionDigits: 0 })} GWh`}
              labelFormatter={(label) => `Período: ${label}`}
              contentStyle={{ backgroundColor: 'rgba(0, 0, 0, 0.8)', border: '1px solid #ccc', borderRadius: '4px' }}
            />
            <Bar dataKey="valor" fill="#3b82f6" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="stats stats-vertical lg:stats-horizontal shadow w-full">
        <div className="stat">
          <div className="stat-title">Total Registros</div>
          <div className="stat-value text-primary">{data.length.toLocaleString()}</div>
          <div className="stat-desc">Datos cargados</div>
        </div>
        <div className="stat">
          <div className="stat-title">Años Cubiertos</div>
          <div className="stat-value text-secondary">
            {new Set(data.map(d => d.period_key.split('-')[0])).size}
          </div>
          <div className="stat-desc">Período de proyección</div>
        </div>
        <div className="stat">
          <div className="stat-title">Última Revisión</div>
          <div className="stat-value text-accent">
            {new Set(data.map(d => d.revision)).size}
          </div>
          <div className="stat-desc">Revisiones disponibles</div>
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

