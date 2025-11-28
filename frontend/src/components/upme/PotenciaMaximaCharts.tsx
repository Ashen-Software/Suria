import { useQuery } from '@tanstack/react-query';
import { loadPotenciaMaximaData } from '@/services/upmeData.service';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { useMemo } from 'react';

export function PotenciaMaximaCharts() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['potencia-maxima'],
    queryFn: loadPotenciaMaximaData,
  });

  const chartData = useMemo(() => {
    if (!data) return [];

    // Verificar qué escenarios realmente existen en los datos
    const availableScenarios = new Set(data.map(r => r.escenario));
    
    const grouped = new Map<string, { year: string; ESC_BAJO: number[]; ESC_MEDIO: number[]; ESC_ALTO: number[] }>();

    data.forEach(record => {
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

  // Datos mensuales detallados
  const monthlyData = useMemo(() => {
    if (!data) return [];

    return data
      .filter(r => r.periodicidad === 'mensual' && r.escenario === 'ESC_MEDIO')
      .map(r => ({
        date: r.period_key,
        month: new Date(r.period_key).toLocaleDateString('es-ES', { month: 'short', year: 'numeric' }),
        valor: r.valor,
      }))
      .sort((a, b) => a.date.localeCompare(b.date))
      .slice(-36); // Últimos 36 meses
  }, [data]);

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
        <span>Error al cargar datos de potencia máxima</span>
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
          <div className="stat-value text-primary">{data.length.toLocaleString()}</div>
        </div>
        <div className="stat">
          <div className="stat-title">Potencia Máxima Promedio</div>
          <div className="stat-value text-secondary">
            {Math.round(data.reduce((sum, d) => sum + d.valor, 0) / data.length).toLocaleString()} MW
          </div>
        </div>
        <div className="stat">
          <div className="stat-title">Período</div>
          <div className="stat-value text-accent">
            {new Set(data.map(d => d.year_span)).size}
          </div>
          <div className="stat-desc">Rangos de años</div>
        </div>
      </div>
    </div>
  );
}

