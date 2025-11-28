/**
 * ChatbotWindow Property-Based Tests
 * 
 * Property-based tests for the ChatbotWindow component using fast-check.
 * Tests verify correctness properties defined in the design document.
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import { BrowserRouter } from 'react-router'
import * as fc from 'fast-check'
import { ChatbotProvider } from '@/contexts/ChatbotContext'
import { ChatbotWindow } from './ChatbotWindow'
import { ChatbotButton } from './ChatbotButton'

/**
 * Wrapper component for testing with router and context
 */
function createWrapper() {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <BrowserRouter>
        <ChatbotProvider>{children}</ChatbotProvider>
      </BrowserRouter>
    )
  }
}

/**
 * Clear sessionStorage before each test
 */
beforeEach(() => {
  sessionStorage.clear()
})

/**
 * Clean up after each test
 */
afterEach(() => {
  sessionStorage.clear()
})

/**
 * **Feature: chatbot-integration, Property 1: Widget state toggle**
 * **Validates: Requirements 1.1, 1.2**
 * 
 * For any initial state of the chatbot widget (open or closed),
 * clicking the toggle button should change the state to its opposite.
 */
describe('Property 1: Widget state toggle', () => {
  it('should toggle widget state from any initial state', () => {
    fc.assert(
      fc.property(fc.boolean(), (initialIsOpen) => {
        // Set initial state in sessionStorage
        const initialState = {
          isOpen: initialIsOpen,
          messages: []
        }
        sessionStorage.setItem('chatbot-state', JSON.stringify(initialState))
        
        // Render both button and window
        const Wrapper = createWrapper()
        const { unmount } = render(
          <Wrapper>
            <ChatbotButton />
            <ChatbotWindow />
          </Wrapper>
        )
        
        // Get the chatbot window element
        const chatbotWindow = screen.getByTestId('chatbot-window')
        
        // Verify initial state
        if (initialIsOpen) {
          // Window should be visible (not have pointer-events-none class)
          expect(chatbotWindow.className).not.toContain('pointer-events-none')
          expect(chatbotWindow.getAttribute('aria-hidden')).toBe('false')
        } else {
          // Window should be hidden (have pointer-events-none class)
          expect(chatbotWindow.className).toContain('pointer-events-none')
          expect(chatbotWindow.getAttribute('aria-hidden')).toBe('true')
        }
        
        // Find and click the toggle button
        const toggleButton = screen.getByLabelText('Abrir asistente virtual')
        act(() => {
          toggleButton.click()
        })
        
        // Verify state changed to opposite
        if (initialIsOpen) {
          // Should now be closed
          expect(chatbotWindow.className).toContain('pointer-events-none')
          expect(chatbotWindow.getAttribute('aria-hidden')).toBe('true')
        } else {
          // Should now be open
          expect(chatbotWindow.className).not.toContain('pointer-events-none')
          expect(chatbotWindow.getAttribute('aria-hidden')).toBe('false')
        }
        
        // Click again to toggle back
        act(() => {
          toggleButton.click()
        })
        
        // Verify state returned to initial
        if (initialIsOpen) {
          // Should be open again
          expect(chatbotWindow.className).not.toContain('pointer-events-none')
          expect(chatbotWindow.getAttribute('aria-hidden')).toBe('false')
        } else {
          // Should be closed again
          expect(chatbotWindow.className).toContain('pointer-events-none')
          expect(chatbotWindow.getAttribute('aria-hidden')).toBe('true')
        }
        
        unmount()
      }),
      { numRuns: 100 }
    )
  })
  
  it('should toggle using close button in header when open', () => {
    fc.assert(
      fc.property(fc.constant(true), (initialIsOpen) => {
        // Set initial state to open
        const initialState = {
          isOpen: initialIsOpen,
          messages: []
        }
        sessionStorage.setItem('chatbot-state', JSON.stringify(initialState))
        
        // Render both button and window
        const Wrapper = createWrapper()
        const { unmount } = render(
          <Wrapper>
            <ChatbotButton />
            <ChatbotWindow />
          </Wrapper>
        )
        
        // Get the chatbot window element
        const chatbotWindow = screen.getByTestId('chatbot-window')
        
        // Verify initial state is open
        expect(chatbotWindow.className).not.toContain('pointer-events-none')
        expect(chatbotWindow.getAttribute('aria-hidden')).toBe('false')
        
        // Find and click the close button in header
        const closeButton = screen.getByTestId('close-button')
        act(() => {
          closeButton.click()
        })
        
        // Verify state changed to closed
        expect(chatbotWindow.className).toContain('pointer-events-none')
        expect(chatbotWindow.getAttribute('aria-hidden')).toBe('true')
        
        unmount()
      }),
      { numRuns: 100 }
    )
  })
})
