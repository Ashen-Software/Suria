import { useQuery } from '@tanstack/react-query';
import { loadCapacidadInstaladaData } from '@/services/upmeData.service';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { useMemo } from 'react';

export function CapacidadInstaladaCharts() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['capacidad-instalada'],
    queryFn: loadCapacidadInstaladaData,
  });

  const chartData = useMemo(() => {
    if (!data) return [];

    // Verificar qué escenarios realmente existen en los datos
    const availableScenarios = new Set(data.map(r => r.escenario));
    
    const grouped = new Map<string, { year: string; ESC_BAJO?: number; ESC_MEDIO?: number; ESC_ALTO?: number }>();

    data.forEach(record => {
      const year = record.period_key.split('-')[0];
      const key = year;
      
      if (!grouped.has(key)) {
        grouped.set(key, { year });
      }
      
      const entry = grouped.get(key)!;
      // Para capacidad, tomamos el máximo del año
      if (!entry[record.escenario] || record.valor > (entry[record.escenario] || 0)) {
        entry[record.escenario] = record.valor;
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

  // Comparación de escenarios para el último año
  const lastYearComparison = useMemo(() => {
    if (!chartData || chartData.length === 0) return [];
    const last = chartData[chartData.length - 1];
    const comparison = [];
    if (last.ESC_BAJO !== null && last.ESC_BAJO !== undefined) {
      comparison.push({ name: 'Escenario Bajo', valor: last.ESC_BAJO, color: '#ef4444' });
    }
    if (last.ESC_MEDIO !== null && last.ESC_MEDIO !== undefined) {
      comparison.push({ name: 'Escenario Medio', valor: last.ESC_MEDIO, color: '#3b82f6' });
    }
    if (last.ESC_ALTO !== null && last.ESC_ALTO !== undefined) {
      comparison.push({ name: 'Escenario Alto', valor: last.ESC_ALTO, color: '#10b981' });
    }
    return comparison;
  }, [chartData]);

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
        <span>Error al cargar datos de capacidad instalada</span>
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
        <h3 className="text-xl font-semibold mb-4">Evolución de Capacidad Instalada por Escenario</h3>
        <p className="text-sm text-base-content/70 mb-4">
          Capacidad instalada proyectada en MW
        </p>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" />
            <YAxis label={{ value: 'MW', angle: -90, position: 'insideLeft' }} />
            <Tooltip 
              formatter={(value: number | null) => {
                if (value === null || value === undefined) return 'N/A';
                return `${value.toLocaleString('es-ES', { maximumFractionDigits: 0 })} MW`;
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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-panel p-6">
          <h3 className="text-xl font-semibold mb-4">Comparación de Escenarios (Último Año)</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={lastYearComparison}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis label={{ value: 'MW', angle: -90, position: 'insideLeft' }} />
              <Tooltip formatter={(value: number) => `${value.toLocaleString('es-ES', { maximumFractionDigits: 0 })} MW`} />
              <Bar dataKey="valor" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="stats stats-vertical shadow">
          <div className="stat">
            <div className="stat-title">Total Registros</div>
            <div className="stat-value text-primary">{data.length.toLocaleString()}</div>
          </div>
          <div className="stat">
            <div className="stat-title">Capacidad Máxima</div>
            <div className="stat-value text-secondary">
              {Math.round(Math.max(...data.map(d => d.valor))).toLocaleString()} MW
            </div>
          </div>
          <div className="stat">
            <div className="stat-title">Capacidad Promedio</div>
            <div className="stat-value text-accent">
              {Math.round(data.reduce((sum, d) => sum + d.valor, 0) / data.length).toLocaleString()} MW
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

