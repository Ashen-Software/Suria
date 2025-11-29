const highlights = [
  { title: 'Automatización diaria', body: 'Monitorea ejecuciones ETL, descubre cuellos de botella y valida resultados desde un único panel.' },
  { title: 'Dimensiones listas', body: 'Accede a los catálogos de tiempo y territorios con filtros, ordenamientos y paginación nativa.' },
  { title: 'Configuraciones trazables', body: 'Registra credenciales, cron y opciones de almacenamiento sin abandonar la vista principal.' },
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
        <div className="absolute inset-0 bg-gradient-to-r from-base-100/95 via-base-100/80 to-base-100/10" aria-hidden="true" />

        <div className="relative z-10 px-6 py-10 md:px-12 md:py-16 flex items-center">
          <div className="mx-auto max-w-3xl space-y-6 text-center md:text-left">
            <div className="space-y-3">
              <p className="text-sm uppercase tracking-[0.3em] text-base-content/60">Bienvenida</p>
              <h2 className="text-gradient text-4xl md:text-5xl font-semibold leading-tight">
                Fuente Centralizada de Datos Suria
              </h2>
            </div>

            <p className="text-lg text-base-content/80">
              Esta plataforma es una fuente centralizada que consolida y gestiona todas tus fuentes de datos ETL en un único lugar. 
              Desde aquí puedes monitorear ejecuciones, ajustar configuraciones, consultar dimensiones y mantener un control completo 
              sobre tu pipeline de datos.
            </p>

            <p className="text-base text-base-content/70">
              Además, cuenta con un <strong>chatbot integrado</strong> que funciona como tu asistente personal. Este asistente te guía 
              por la plataforma, responde tus preguntas y te ayuda a navegar y utilizar todas las funcionalidades disponibles de manera eficiente.
            </p>

            <div className="flex flex-wrap justify-center md:justify-start gap-3 mt-2">
              <span className="badge badge-primary badge-outline px-4 py-3 text-sm">Fuente centralizada</span>
              <span className="badge badge-secondary badge-outline px-4 py-3 text-sm">Asistente con chatbot</span>
              <span className="badge badge-accent badge-outline px-4 py-3 text-sm">Gestión unificada</span>
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