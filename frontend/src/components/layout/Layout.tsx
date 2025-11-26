import { ReactNode } from 'react';
import { Header } from './Header';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-base-100">
      <Header />
      <main className="container mx-auto p-4">
        {children}
      </main>
    </div>
  );
}
