import { useEffect, useState } from 'react'

const THEMES = [
  { id: 'corporate', label: 'Claro' },
  { id: 'dark', label: 'Oscuro' },
]

export function Header() {
  const [theme, setTheme] = useState<string>('dark')

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 'dark'
    setTheme(savedTheme)
    document.documentElement.setAttribute('data-theme', savedTheme)
  }, [])

  const handleThemeChange = (newTheme: string) => {
    setTheme(newTheme)
    localStorage.setItem('theme', newTheme)
    document.documentElement.setAttribute('data-theme', newTheme)
  }

  return (
    <header className="glass-panel flex flex-wrap items-center justify-between gap-4 px-5 py-4">
      <div className="flex items-center gap-4">
        <div className="relative flex h-12 w-12 items-center justify-center rounded-2xl overflow-hidden">
          <img 
            src="/favicon.svg" 
            alt="Suria Logo" 
            className="w-full h-full object-contain"
          />
          <span className="pointer-events-none absolute inset-0 rounded-2xl border border-primary/30 motion-safe:animate-ping" aria-hidden="true" />
        </div>
        <div>
          <p className="text-sm uppercase tracking-wide text-base-content/60">Plataforma Suria</p>
          <h1 className="text-gradient text-2xl font-semibold tracking-tight">Panel de control ETL</h1>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <span className="text-sm text-base-content/60">Tema</span>
        <div className="flex items-center gap-2 rounded-full bg-base-200/70 p-1">
          {THEMES.map(({ id, label }) => (
            <button
              key={id}
              type="button"
              onClick={() => handleThemeChange(id)}
              aria-pressed={theme === id}
              className={`flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition ${
                theme === id ? 'bg-base-100 shadow-lg shadow-primary/10 text-primary' : 'text-base-content/70 hover:text-base-content'
              }`}
            >
              {id === 'corporate' ? (
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <circle cx="12" cy="12" r="5" strokeWidth="1.5" />
                  <path d="M12 2v2m0 16v2m10-10h-2M4 12H2m15.536-7.536-1.414 1.414M7.879 16.95l-1.414 1.414m0-12.728 1.414 1.414m9.193 9.193 1.414 1.414" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <path d="M21 12.79A9 9 0 1 1 11.21 3a7 7 0 0 0 9.79 9.79Z" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              )}
              <span>{label}</span>
            </button>
          ))}
        </div>
      </div>
    </header>
  )
}
