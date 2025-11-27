import { useEffect, useState, type CSSProperties, type ReactNode } from 'react'
import { Header } from './Header'

interface LayoutProps {
  children: ReactNode
}

export function Layout({ children }: LayoutProps) {
  const [pointer, setPointer] = useState({ x: 0, y: 0 })

  useEffect(() => {
    const handlePointer = (event: PointerEvent) => {
      setPointer({ x: event.clientX, y: event.clientY })
    }

    window.addEventListener('pointermove', handlePointer, { passive: true })
    return () => window.removeEventListener('pointermove', handlePointer)
  }, [])

  const glowStyle: CSSProperties = {
    transform: `translate3d(${pointer.x - 200}px, ${pointer.y - 200}px, 0)`,
    opacity: pointer.x === 0 && pointer.y === 0 ? 0 : 1,
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-base-100 text-base-content">
      <div className="pointer-events-none absolute inset-0">
        <div
          className="absolute h-[26rem] w-[26rem] rounded-full bg-primary/25 blur-[140px] transition duration-500 ease-out"
          style={glowStyle}
        />
      </div>
      <div className="pointer-events-none absolute inset-x-0 top-0 h-[620px] opacity-70 blur-3xl">
        <div className="absolute left-1/2 top-0 h-72 w-72 -translate-x-1/2 rounded-full bg-primary/30 animate-ring" />
        <div className="absolute right-16 top-16 h-60 w-60 rounded-full bg-secondary/20 animate-float" />
        <div className="absolute left-12 top-32 h-40 w-40 rounded-[32px] border border-base-200/30" />
      </div>

      <div className="relative z-10 mx-auto flex min-h-screen w-full max-w-[1440px] flex-col gap-6 px-4 py-6 md:px-8 lg:px-10">
        <Header />
        <main className="flex-1 pb-8">{children}</main>
      </div>
    </div>
  )
}
