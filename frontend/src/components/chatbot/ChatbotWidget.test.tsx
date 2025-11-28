/**
 * ChatbotWidget Component Tests
 * 
 * Tests for the main ChatbotWidget component including:
 * - Conditional rendering based on open/closed state
 * - Keyboard shortcuts (Escape to close)
 * - Integration with ChatbotContext
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router'
import { ChatbotWidget } from './ChatbotWidget'
import { ChatbotProvider } from '@/contexts/ChatbotContext'

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

describe('ChatbotWidget', () => {
  beforeEach(() => {
    // Clear any stored state
    sessionStorage.clear()
  })
  
  it('should render the floating button when closed', () => {
    render(<ChatbotWidget />, { wrapper: Wrapper })
    
    // Button should be visible
    const button = screen.getByRole('button', { name: /abrir asistente virtual/i })
    expect(button).toBeDefined()
    
    // Window should not be visible (has pointer-events-none and opacity-0)
    const window = screen.getByTestId('chatbot-window')
    expect(window.className).toContain('pointer-events-none')
    expect(window.className).toContain('opacity-0')
  })
  
  it('should show the chat window when button is clicked', () => {
    render(<ChatbotWidget />, { wrapper: Wrapper })
    
    // Click the button
    const button = screen.getByRole('button', { name: /abrir asistente virtual/i })
    fireEvent.click(button)
    
    // Window should now be visible
    const window = screen.getByTestId('chatbot-window')
    expect(window.className).not.toContain('pointer-events-none')
    expect(window.className).not.toContain('opacity-0')
    
    // Button should not be visible
    const buttonAfter = screen.queryByRole('button', { name: /abrir asistente virtual/i })
    expect(buttonAfter).toBeNull()
  })
  
  it('should close the chat window when Escape key is pressed', () => {
    render(<ChatbotWidget />, { wrapper: Wrapper })
    
    // Open the chatbot
    const button = screen.getByRole('button', { name: /abrir asistente virtual/i })
    fireEvent.click(button)
    
    // Verify it's open
    let window = screen.getByTestId('chatbot-window')
    expect(window.className).not.toContain('pointer-events-none')
    
    // Press Escape on the window element
    fireEvent.keyDown(window, { key: 'Escape', code: 'Escape' })
    
    // Window should be closed
    window = screen.getByTestId('chatbot-window')
    expect(window.className).toContain('pointer-events-none')
    expect(window.className).toContain('opacity-0')
  })
  
  it('should not close when Escape is pressed while chatbot is already closed', () => {
    render(<ChatbotWidget />, { wrapper: Wrapper })
    
    // Chatbot is closed by default
    const button = screen.getByRole('button', { name: /abrir asistente virtual/i })
    expect(button).toBeDefined()
    
    // Press Escape on document
    fireEvent.keyDown(document, { key: 'Escape', code: 'Escape' })
    
    // Button should still be visible (no change)
    const buttonAfter = screen.getByRole('button', { name: /abrir asistente virtual/i })
    expect(buttonAfter).toBeDefined()
  })
  
  it('should maintain state across re-renders', () => {
    const { rerender } = render(<ChatbotWidget />, { wrapper: Wrapper })
    
    // Open the chatbot
    const button = screen.getByRole('button', { name: /abrir asistente virtual/i })
    fireEvent.click(button)
    
    // Verify it's open
    let window = screen.getByTestId('chatbot-window')
    expect(window.className).not.toContain('pointer-events-none')
    
    // Re-render
    rerender(<ChatbotWidget />)
    
    // Should still be open
    window = screen.getByTestId('chatbot-window')
    expect(window.className).not.toContain('pointer-events-none')
  })
  
  it('should integrate with ChatbotContext for state management', () => {
    render(<ChatbotWidget />, { wrapper: Wrapper })
    
    // Initial state: closed
    const button = screen.getByRole('button', { name: /abrir asistente virtual/i })
    expect(button).toBeDefined()
    
    // Toggle open
    fireEvent.click(button)
    
    // State should be open
    const window = screen.getByTestId('chatbot-window')
    expect(window.className).not.toContain('pointer-events-none')
    
    // Close via header button
    const closeButton = screen.getByRole('button', { name: /cerrar/i })
    fireEvent.click(closeButton)
    
    // State should be closed
    expect(window.className).toContain('pointer-events-none')
  })
})
