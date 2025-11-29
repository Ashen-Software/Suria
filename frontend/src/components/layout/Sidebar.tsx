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
    path: '/integrado',
    label: 'Integrado',
    helper: 'Visión cruzada gas, electricidad y regalías',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M4 6h7v7H4V6zm9 0h7v7h-7V6zM4 16h7v2H4v-2zm9 0h7v2h-7v-2z"
        />
      </svg>
    ),
  },
  {
    path: '/regalias',
    label: 'Regalías',
    helper: 'Liquidación de regalías',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-10v2m0 8v2m-7-2a9 9 0 1114 0 9 9 0 01-14 0z"
        />
      </svg>
    ),
  },
  {
    path: '/declaracion-gas',
    label: 'Declaración de Gas',
    helper: 'Oferta de gas natural',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M11 3v2m0 14v2m7-9h2M3 12H1m15.364-6.364l1.414 1.414M5.222 18.778l-1.414-1.414M18.778 18.778l-1.414-1.414M5.222 5.222L3.808 3.808M12 8c-2.21 0-4 1.343-4 3s1.79 3 4 3 4 1.343 4 3-1.79 3-4 3"
        />
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
  {
    path: '/dimensiones',
    label: 'Dimensiones',
    helper: 'Tiempo y territorios',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M4 6h16M4 12h16M4 18h7"
        />
      </svg>
    ),
  },
]

export function Sidebar() {
  return (
    <aside className="glass-panel w-full shrink-0 space-y-6 p-6 lg:w-72">
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
