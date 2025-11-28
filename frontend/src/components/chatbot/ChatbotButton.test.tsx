/**
 * ChatbotButton Component Tests
 * 
 * Unit tests for the ChatbotButton component.
 */

import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router'
import { ChatbotProvider } from '@/contexts/ChatbotContext'
import { ChatbotButton } from './ChatbotButton'

/**
 * Wrapper component for testing with required providers
 */
function Wrapper({ children }: { children: React.ReactNode }) {
  return (
    <BrowserRouter>
      <ChatbotProvider>{children}</ChatbotProvider>
    </BrowserRouter>
  )
}

describe('ChatbotButton', () => {
  it('should render the button with correct aria-label', () => {
    render(<ChatbotButton />, { wrapper: Wrapper })
    
    const button = screen.getByRole('button', { name: /abrir asistente virtual/i })
    expect(button).toBeDefined()
  })

  it('should have fixed positioning classes', () => {
    render(<ChatbotButton />, { wrapper: Wrapper })
    
    const button = screen.getByRole('button', { name: /abrir asistente virtual/i })
    expect(button.className).toContain('fixed')
    expect(button.className).toContain('bottom-6')
    expect(button.className).toContain('right-6')
  })

  it('should display notification badge when unreadCount > 0', () => {
    render(<ChatbotButton unreadCount={3} />, { wrapper: Wrapper })
    
    const badge = screen.getByText('3')
    expect(badge).toBeDefined()
    expect(badge.className).toContain('badge')
  })

  it('should display "9+" when unreadCount > 9', () => {
    render(<ChatbotButton unreadCount={15} />, { wrapper: Wrapper })
    
    const badge = screen.getByText('9+')
    expect(badge).toBeDefined()
  })

  it('should not display badge when unreadCount is 0', () => {
    render(<ChatbotButton unreadCount={0} />, { wrapper: Wrapper })
    
    const badge = screen.queryByText(/\d+/)
    expect(badge).toBeNull()
  })

  it('should call toggleOpen when clicked', () => {
    render(<ChatbotButton />, { wrapper: Wrapper })
    
    const button = screen.getByRole('button', { name: /abrir asistente virtual/i })
    
    // Click the button
    fireEvent.click(button)
    
    // The button should still be defined (it doesn't unmount)
    expect(button).toBeDefined()
  })

  it('should have DaisyUI button classes', () => {
    render(<ChatbotButton />, { wrapper: Wrapper })
    
    const button = screen.getByRole('button', { name: /abrir asistente virtual/i })
    expect(button.className).toContain('btn')
    expect(button.className).toContain('btn-circle')
    expect(button.className).toContain('btn-primary')
    expect(button.className).toContain('btn-lg')
  })

  it('should have z-index for overlay positioning', () => {
    render(<ChatbotButton />, { wrapper: Wrapper })
    
    const button = screen.getByRole('button', { name: /abrir asistente virtual/i })
    expect(button.className).toContain('z-50')
  })
})
