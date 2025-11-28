const highlights = [
  { title: 'Automatización diaria', body: 'Monitorea ejecuciones ETL, descubre cuellos de botella y valida resultados desde un único panel.' },
  { title: 'Dimensiones listas', body: 'Accede a los catálogos de tiempo y territorios con filtros, ordenamientos y paginación nativa.' },
  { title: 'Configuraciones trazables', body: 'Registra credenciales, cron y opciones de almacenamiento sin abandonar la vista principal.' },
]

export function HomePage() {
  return (
    <div className="space-y-8">
      <section className="interactive-tile overflow-hidden">
        <div className="absolute inset-0 bg-grid-pattern opacity-10" aria-hidden="true" />
        <div className="relative z-10 flex flex-col gap-6 md:flex-row md:items-center">
          <div className="space-y-4 md:flex-1">
            <p className="text-sm uppercase tracking-[0.3em] text-base-content/60">Bienvenida</p>
            <h2 className="text-gradient text-4xl font-semibold leading-tight">Control total sobre tus fuentes Suria</h2>
            <p className="text-base text-base-content/70">
              Revisa ejecuciones, ajusta cron y consulta dimensiones directamente desde la plataforma para reaccionar a cualquier variación del pipeline.
            </p>
            <div className="flex flex-wrap gap-3">
              <span className="badge badge-primary badge-outline px-4 py-3 text-sm">Seguimiento en tiempo casi real</span>
              <span className="badge badge-secondary badge-outline px-4 py-3 text-sm">Edición centralizada</span>
            </div>
          </div>
          <div className="glass-panel relative flex flex-col gap-3 rounded-3xl p-6 md:w-80">
            <div className="space-y-1">
              <p className="text-sm text-base-content/60">Estado general</p>
              <p className="text-3xl font-semibold">Estable</p>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-base-content/70">Fuentes activas</span>
              <span className="text-lg font-semibold text-primary">32</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-base-content/70">Última ejecución</span>
              <span className="text-lg font-semibold">08:45</span>
            </div>
            <div className="mt-4 h-24 rounded-2xl bg-gradient-to-br from-primary/20 via-secondary/10 to-transparent" />
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {highlights.map((feature) => (
          <article key={feature.title} className="soft-card hover:-translate-y-1">
            <p className="text-sm uppercase tracking-[0.2em] text-base-content/50">{feature.title}</p>
            <p className="mt-3 text-base text-base-content/80">{feature.body}</p>
          </article>
        ))}
      </section>
    </div>
  )
}