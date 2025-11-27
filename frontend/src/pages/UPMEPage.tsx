export function UPMEPage() {
  const lookerStudioUrl = "https://lookerstudio.google.com/embed/reporting/7204226d-5cae-48ca-a261-c85745ffd102/page/p_8a8596htwc"

  return (
    <div className="space-y-6">
      <section className="space-y-4">
        <div className="space-y-2">
          <p className="text-sm uppercase tracking-[0.2em] text-base-content/50">Visualización</p>
          <h2 className="text-gradient text-3xl font-semibold">Dashboard UPME</h2>
          <p className="text-base text-base-content/70">
            Reportes y visualizaciones interactivas de la Unidad de Planeación Minero Energética
          </p>
        </div>
      </section>

      <div className="glass-panel overflow-hidden p-6">
        <div className="relative w-full mx-auto max-w-7xl" style={{ minHeight: '600px', height: '600px' }}>
          <iframe
            src={lookerStudioUrl}
            className="absolute inset-0 w-full h-full border-0 rounded-2xl"
            allowFullScreen
            title="Dashboard UPME"
            loading="lazy"
          />
        </div>
      </div>
    </div>
  )
}

