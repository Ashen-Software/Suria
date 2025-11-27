import { Outlet, useLocation } from 'react-router'
import { Sidebar } from './Sidebar'

export function MainLayout() {
  const location = useLocation()

  return (
    <div className="flex flex-col gap-6 lg:flex-row">
      <Sidebar />
      <main className="glass-panel flex-1 overflow-hidden p-4 md:p-8">
        <div key={location.pathname} className="h-full animate-fade-up">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
