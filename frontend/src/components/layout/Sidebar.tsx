import { NavLink } from 'react-router'

interface NavItem {
  path: string
  label: string
  icon: React.ReactNode
  helper: string
}

const navItems: NavItem[] = [
  {
    path: '/',
    label: 'Inicio',
    helper: 'Resumen principal',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      </svg>
    ),
  },
  {
    path: '/etl',
    label: 'Fuentes ETL',
    helper: 'Gestión completa',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
      </svg>
    ),
  },
  {
    path: '/tiempo',
    label: 'Dimensión Tiempo',
    helper: 'Calendario maestro',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
    ),
  },
  {
    path: '/territorios',
    label: 'Dimensión Territorios',
    helper: 'Mapa administrativo',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
  },
  {
    path: '/upme',
    label: 'UPME',
    helper: 'Reportes y visualizaciones',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
  },
]

export function Sidebar() {
  return (
    <aside className="glass-panel w-full flex-shrink-0 space-y-6 p-6 lg:w-72">
      <div className="space-y-1">
        <p className="text-sm uppercase tracking-[0.2em] text-base-content/50">Navegación</p>
        <h2 className="text-2xl font-semibold">Explora el flujo</h2>
      </div>

      <nav className="space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `group relative flex flex-col gap-1 rounded-2xl border border-transparent px-4 py-3 transition ${
                isActive ? 'border-primary/40 bg-primary/10 text-primary shadow-lg shadow-primary/10' : 'hover:border-base-200/80 hover:bg-base-200/50'
              }`
            }
          >
            <div className="flex items-center gap-3 text-sm font-semibold">
              <span className="rounded-xl bg-base-200/70 p-2 text-base-content/70 transition group-hover:text-primary">{item.icon}</span>
              {item.label}
            </div>
            <span className="text-xs text-base-content/60">{item.helper}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
