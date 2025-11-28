/**
 * ChatInput Component Tests
 * 
 * Unit tests and property-based tests for the ChatInput component.
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router'
import { ChatbotProvider } from '@/contexts/ChatbotContext'
import { ChatInput } from './ChatInput'
import * as fc from 'fast-check'

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

describe('ChatInput', () => {
  beforeEach(() => {
    // Clear sessionStorage before each test
    sessionStorage.clear()
  })

  it('should render textarea and send button', () => {
    render(<ChatInput />, { wrapper: Wrapper })
    
    const textarea = screen.getByTestId('chat-input')
    const sendButton = screen.getByTestId('send-button')
    
    expect(textarea).toBeDefined()
    expect(sendButton).toBeDefined()
  })

  it('should update input value when typing', () => {
    render(<ChatInput />, { wrapper: Wrapper })
    
    const textarea = screen.getByTestId('chat-input') as HTMLTextAreaElement
    
    fireEvent.change(textarea, { target: { value: 'Hello' } })
    
    expect(textarea.value).toBe('Hello')
  })

  it('should disable send button when input is empty', () => {
    render(<ChatInput />, { wrapper: Wrapper })
    
    const sendButton = screen.getByTestId('send-button') as HTMLButtonElement
    
    expect(sendButton.disabled).toBe(true)
  })

  it('should enable send button when input has valid content', () => {
    render(<ChatInput />, { wrapper: Wrapper })
    
    const textarea = screen.getByTestId('chat-input') as HTMLTextAreaElement
    const sendButton = screen.getByTestId('send-button') as HTMLButtonElement
    
    fireEvent.change(textarea, { target: { value: 'Hello' } })
    
    expect(sendButton.disabled).toBe(false)
  })

  it('should disable send button when input is only whitespace', () => {
    render(<ChatInput />, { wrapper: Wrapper })
    
    const textarea = screen.getByTestId('chat-input') as HTMLTextAreaElement
    const sendButton = screen.getByTestId('send-button') as HTMLButtonElement
    
    fireEvent.change(textarea, { target: { value: '   ' } })
    
    expect(sendButton.disabled).toBe(true)
  })

  it('should send message when send button is clicked', async () => {
    render(<ChatInput />, { wrapper: Wrapper })
    
    const textarea = screen.getByTestId('chat-input') as HTMLTextAreaElement
    const sendButton = screen.getByTestId('send-button')
    
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)
    
    // Input should be cleared immediately
    expect(textarea.value).toBe('')
  })

  it('should send message when Enter key is pressed', async () => {
    render(<ChatInput />, { wrapper: Wrapper })
    
    const textarea = screen.getByTestId('chat-input') as HTMLTextAreaElement
    
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false })
    
    // Input should be cleared immediately
    expect(textarea.value).toBe('')
  })

  it('should add new line when Shift+Enter is pressed', () => {
    render(<ChatInput />, { wrapper: Wrapper })
    
    const textarea = screen.getByTestId('chat-input') as HTMLTextAreaElement
    
    fireEvent.change(textarea, { target: { value: 'Line 1' } })
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: true })
    
    // Input should not be cleared
    expect(textarea.value).toBe('Line 1')
  })

  it('should disable input and button during loading', async () => {
    render(<ChatInput />, { wrapper: Wrapper })
    
    const textarea = screen.getByTestId('chat-input') as HTMLTextAreaElement
    const sendButton = screen.getByTestId('send-button') as HTMLButtonElement
    
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.click(sendButton)
    
    // During loading, both should be disabled
    await waitFor(() => {
      expect(textarea.disabled).toBe(true)
      expect(sendButton.disabled).toBe(true)
    })
  })

  /**
   * Property-Based Test
   * 
   * **Feature: chatbot-integration, Property 4: Input field clearing**
   * **Validates: Requirements 2.2**
   * 
   * For any message sent through the chat input, the input field should be 
   * empty immediately after the message is sent.
   */
  it('Property 4: Input field clearing - for any valid message, input should be cleared after send', () => {
    fc.assert(
      fc.property(
        // Generate non-empty strings with at least one non-whitespace character
        fc.string({ minLength: 1, maxLength: 500 }).filter(s => s.trim().length > 0),
        (message) => {
          // Render component
          const { unmount } = render(<ChatInput />, { wrapper: Wrapper })
          
          const textarea = screen.getByTestId('chat-input') as HTMLTextAreaElement
          const sendButton = screen.getByTestId('send-button')
          
          // Set input value
          fireEvent.change(textarea, { target: { value: message } })
          
          // Verify input has the message
          expect(textarea.value).toBe(message)
          
          // Click send button
          fireEvent.click(sendButton)
          
          // Verify input is cleared immediately
          expect(textarea.value).toBe('')
          
          // Cleanup
          unmount()
        }
      ),
      { numRuns: 100 }
    )
  })
})
