/**
 * ChatHeader Component Tests
 * 
 * Tests for the ChatHeader component functionality
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router'
import { ChatHeader } from './ChatHeader'
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

describe('ChatHeader', () => {
  beforeEach(() => {
    // Clear sessionStorage before each test
    sessionStorage.clear()
  })

  it('renders the title "Asistente Virtual"', () => {
    render(<ChatHeader />, { wrapper: Wrapper })
    
    const title = screen.getByTestId('chat-header-title')
    expect(title).toBeDefined()
    expect(title.textContent).toBe('Asistente Virtual')
  })
  
  it('renders close button', () => {
    render(<ChatHeader />, { wrapper: Wrapper })
    
    const closeButton = screen.getByTestId('close-button')
    expect(closeButton).toBeDefined()
  })
  
  it('renders clear history button', () => {
    render(<ChatHeader />, { wrapper: Wrapper })
    
    const clearButton = screen.getByTestId('clear-history-button')
    expect(clearButton).toBeDefined()
  })
  
  it('shows confirmation dialog when clear history is clicked', () => {
    render(<ChatHeader />, { wrapper: Wrapper })
    
    const clearButton = screen.getByTestId('clear-history-button')
    fireEvent.click(clearButton)
    
    const dialog = screen.getByTestId('confirmation-dialog')
    expect(dialog).toBeDefined()
    
    const dialogText = screen.getByText('¿Limpiar historial?')
    expect(dialogText).toBeDefined()
  })
  
  it('hides confirmation dialog when cancel is clicked', () => {
    render(<ChatHeader />, { wrapper: Wrapper })
    
    // Open confirmation dialog
    const clearButton = screen.getByTestId('clear-history-button')
    fireEvent.click(clearButton)
    
    // Click cancel
    const cancelButton = screen.getByTestId('cancel-clear-button')
    fireEvent.click(cancelButton)
    
    // Dialog should be hidden
    const dialog = screen.queryByTestId('confirmation-dialog')
    expect(dialog).toBeNull()
  })
  
  it('clears history and hides dialog when confirm is clicked', () => {
    render(<ChatHeader />, { wrapper: Wrapper })
    
    // Open confirmation dialog
    const clearButton = screen.getByTestId('clear-history-button')
    fireEvent.click(clearButton)
    
    // Click confirm
    const confirmButton = screen.getByTestId('confirm-clear-button')
    fireEvent.click(confirmButton)
    
    // Dialog should be hidden
    const dialog = screen.queryByTestId('confirmation-dialog')
    expect(dialog).toBeNull()
  })
})
