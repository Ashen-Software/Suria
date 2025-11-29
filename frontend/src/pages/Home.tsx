const highlights = [
  {
    title: 'Visión integrada',
    body: 'Cruza proyecciones UPME, declaración de gas y regalías ANH para entender el sistema energético en un solo panel.',
  },
  {
    title: 'Dashboards especializados',
    body: 'Explora vistas dedicadas para demanda de gas, energía eléctrica, declaración de producción y regalías por campo.',
  },
  {
    title: 'Análisis asistido por IA',
    body: 'Genera resúmenes ejecutivos y análisis predictivos directamente desde los dashboards con un solo clic.',
  },
]

export function HomePage() {
  return (
    <div className="space-y-8">
      <section className="relative overflow-hidden rounded-3xl border border-base-200/60 bg-base-100/80">
        {/* Video de fondo */}
        <video
          className="absolute inset-0 h-full w-full object-cover"
          autoPlay
          loop
          muted
          playsInline
          aria-label="Plataforma Suria - Gestión centralizada de datos ETL"
        >
          <source src="/hero-video.mp4" type="video/mp4" />
        </video>

        {/* Capa de oscurecimiento para legibilidad del texto */}
        <div className="absolute inset-0 bg-linear-to-r from-base-100/95 via-base-100/80 to-base-100/10" aria-hidden="true" />

        <div className="relative z-10 px-6 py-10 md:px-12 md:py-16 flex items-center">
          <div className="mx-auto max-w-3xl space-y-6 text-center md:text-left">
            <div className="space-y-3">
              <p className="text-sm uppercase tracking-[0.3em] text-base-content/60">Bienvenida</p>
              <h2 className="text-gradient text-4xl md:text-5xl font-semibold leading-tight">
                Observatorio Energético Suria
              </h2>
            </div>

            <p className="text-lg text-base-content/80">
              Suria consolida en un solo lugar las principales fuentes públicas de energía de Colombia: proyecciones UPME,
              declaración de gas natural (MinMinas) y regalías por campo (ANH). Desde aquí puedes explorar demanda, oferta,
              capacidad instalada y rentas asociadas sin salir del dashboard.
            </p>

            <p className="text-base text-base-content/70">
              Además, cuenta con un <strong>asistente de IA integrado</strong> que interpreta los indicadores, genera análisis
              predictivos y te ayuda a navegar las vistas integradas y especializadas de forma guiada.
            </p>

            <div className="flex flex-wrap justify-center md:justify-start gap-3 mt-2">
              <span className="badge badge-primary badge-outline px-4 py-3 text-sm">Dashboard integrado</span>
              <span className="badge badge-secondary badge-outline px-4 py-3 text-sm">Analítica energética</span>
              <span className="badge badge-accent badge-outline px-4 py-3 text-sm">IA explicativa</span>
            </div>
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