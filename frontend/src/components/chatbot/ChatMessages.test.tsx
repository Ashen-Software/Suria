/**
 * ChatMessages Component Tests
 * 
 * Property-based tests for the ChatMessages component.
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import * as fc from 'fast-check'
import { ChatMessages } from './ChatMessages'
import type { Message } from '@/types/chatbot.types'

/**
 * Arbitrary generator for Message objects
 */
const arbitraryMessage = (index?: number): fc.Arbitrary<Message> => {
  return fc.record({
    id: fc.constant(index !== undefined ? `test-id-${index}` : 'test-id'),
    role: fc.constantFrom('user' as const, 'assistant' as const),
    content: fc.string({ minLength: 1, maxLength: 200 }).filter(s => s.trim().length > 0),
    // Use integer timestamp to avoid invalid dates
    timestamp: fc.integer({ min: 946684800000, max: 1924905600000 }).map(ts => new Date(ts))
  })
}

/**
 * Arbitrary generator for message arrays (conversation history)
 * Ensures unique IDs for each message
 */
const arbitraryMessageHistory = (): fc.Arbitrary<Message[]> => {
  return fc.array(fc.integer({ min: 0, max: 19 }), { minLength: 1, maxLength: 20 })
    .chain(indices => 
      fc.tuple(...indices.map((_, i) => arbitraryMessage(i)))
    )
}

describe('ChatMessages Component', () => {
  /**
   * Feature: chatbot-integration, Property 9: History display on open
   * Validates: Requirements 4.1
   * 
   * For any existing conversation history, opening the chatbot should display
   * all messages from the current session in chronological order.
   */
  it('Property 9: displays all messages from history in chronological order', () => {
    fc.assert(
      fc.property(arbitraryMessageHistory(), (messages) => {
        // Render the component with the message history
        const { container, unmount } = render(
          <ChatMessages messages={messages} isLoading={false} />
        )
        
        try {
          // Verify that the messages container is rendered
          const messagesContainer = screen.getByTestId('messages-container')
          expect(messagesContainer).toBeDefined()
          
          // Verify that all messages are displayed
          // Each message should have a data-testid based on its role
          const userMessages = container.querySelectorAll('[data-testid="message-user"]')
          const assistantMessages = container.querySelectorAll('[data-testid="message-assistant"]')
          
          const expectedUserCount = messages.filter(m => m.role === 'user').length
          const expectedAssistantCount = messages.filter(m => m.role === 'assistant').length
          
          expect(userMessages.length).toBe(expectedUserCount)
          expect(assistantMessages.length).toBe(expectedAssistantCount)
          
          // Verify total message count
          const totalRenderedMessages = userMessages.length + assistantMessages.length
          expect(totalRenderedMessages).toBe(messages.length)
          
          // Verify messages are in chronological order by checking roles
          // We check that the sequence of roles in the DOM matches the input
          const allChatElements = container.querySelectorAll('.chat[data-testid^="message-"]')
          messages.forEach((message, index) => {
            const chatElement = allChatElements[index]
            const expectedTestId = `message-${message.role}`
            expect(chatElement.getAttribute('data-testid')).toBe(expectedTestId)
          })
        } finally {
          // Clean up after each test iteration
          unmount()
        }
      }),
      { numRuns: 100 }
    )
  })

  /**
   * Feature: chatbot-integration, Property 5: Loading state during processing
   * Validates: Requirements 2.3
   * 
   * For any message being processed by the LLM service, the chatbot should
   * display a loading indicator until the response is received or an error occurs.
   */
  it('Property 5: displays loading indicator when isLoading is true', () => {
    fc.assert(
      fc.property(
        fc.array(arbitraryMessage(), { maxLength: 10 }),
        fc.boolean(),
        (messages, isLoading) => {
          // Render the component
          const { unmount } = render(<ChatMessages messages={messages} isLoading={isLoading} />)
          
          try {
            // Check if loading indicator is present based on isLoading state
            const loadingIndicator = screen.queryByTestId('loading-indicator')
            
            if (isLoading) {
              // Loading indicator should be present when isLoading is true
              expect(loadingIndicator).not.toBeNull()
            } else {
              // Loading indicator should not be present when isLoading is false
              expect(loadingIndicator).toBeNull()
            }
          } finally {
            // Clean up after each test iteration
            unmount()
          }
        }
      ),
      { numRuns: 100 }
    )
  })
})
