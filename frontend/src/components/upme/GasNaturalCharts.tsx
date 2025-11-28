import { useQuery } from '@tanstack/react-query';
import { loadGasNaturalData } from '@/services/upmeData.service';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { useMemo, useState } from 'react';

const COLORS = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1'];

export function GasNaturalCharts() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['gas-natural'],
    queryFn: loadGasNaturalData,
  });

  const [selectedCategoria, setSelectedCategoria] = useState<string | null>(null);

  // Obtener todas las categorías disponibles
  const categorias = useMemo(() => {
    if (!data) return [];
    return Array.from(new Set(data.map(d => d.categoria))).sort();
  }, [data]);

  // Datos por categoría y escenario
  const categoriaData = useMemo(() => {
    if (!data) return [];

    const filtered = selectedCategoria 
      ? data.filter(d => d.categoria === selectedCategoria)
      : data;

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
    if (!data) return [];

    const lastYear = Math.max(...data.map(d => parseInt(d.period_key.split('-')[0])));
    const filtered = data.filter(
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
    if (!data || !selectedCategoria) return [];

    return data
      .filter(r => r.categoria === selectedCategoria && r.escenario === 'ESC_MEDIO' && r.periodicidad === 'mensual')
      .map(r => ({
        date: r.period_key,
        month: new Date(r.period_key).toLocaleDateString('es-ES', { month: 'short', year: 'numeric' }),
        valor: r.valor,
      }))
      .sort((a, b) => a.date.localeCompare(b.date))
      .slice(-24); // Últimos 24 meses
  }, [data, selectedCategoria]);

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
        <span>Error al cargar datos de gas natural</span>
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
            <div className="stat-value text-primary">{data.length.toLocaleString()}</div>
          </div>
          <div className="stat">
            <div className="stat-title">Categorías</div>
            <div className="stat-value text-secondary">{categorias.length}</div>
          </div>
          <div className="stat">
            <div className="stat-title">Demanda Total Promedio</div>
            <div className="stat-value text-accent">
              {Math.round(data.reduce((sum, d) => sum + d.valor, 0) / data.length).toLocaleString()} GBTUD
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

