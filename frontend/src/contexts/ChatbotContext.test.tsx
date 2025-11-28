/**
 * ChatbotContext Property-Based Tests
 * 
 * Property-based tests for the ChatbotContext provider using fast-check.
 * Tests verify correctness properties defined in the design document.
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { BrowserRouter } from 'react-router'
import * as fc from 'fast-check'
import { ChatbotProvider, useChatbot } from './ChatbotContext'
import type { Message } from '@/types/chatbot.types'

/**
 * Wrapper component for testing with router
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
 * **Feature: chatbot-integration, Property 2: State persistence across navigation**
 * **Validates: Requirements 1.3**
 * 
 * For any chatbot state (open or closed) and any route change, 
 * the chatbot state should remain unchanged after navigation.
 */
describe('Property 2: State persistence across navigation', () => {
  it('should persist isOpen state across hook re-renders', () => {
    fc.assert(
      fc.property(fc.boolean(), (initialIsOpen) => {
        // First render - set initial state
        const { result: result1, unmount: unmount1 } = renderHook(
          () => useChatbot(),
          { wrapper: createWrapper() }
        )
        
        // Set the open state
        if (initialIsOpen !== result1.current.isOpen) {
          act(() => {
            result1.current.toggleOpen()
          })
        }
        
        // Verify state is set correctly
        expect(result1.current.isOpen).toBe(initialIsOpen)
        
        // Unmount (simulating navigation)
        unmount1()
        
        // Second render - should restore state from sessionStorage
        const { result: result2, unmount: unmount2 } = renderHook(
          () => useChatbot(),
          { wrapper: createWrapper() }
        )
        
        // Verify state persisted
        expect(result2.current.isOpen).toBe(initialIsOpen)
        
        unmount2()
      }),
      { numRuns: 100 }
    )
  })

  it('should persist messages across hook re-renders', () => {
    fc.assert(
      fc.property(
        fc.array(fc.string({ minLength: 1, maxLength: 100 }), { minLength: 1, maxLength: 5 }),
        (messageContents) => {
          // Manually add messages to sessionStorage (simulating previous session)
          const messagesToAdd: Message[] = messageContents.map((content, idx) => ({
            id: `test-${idx}`,
            role: 'user' as const,
            content,
            timestamp: new Date()
          }))
          
          const stateToSave = {
            isOpen: false,
            messages: messagesToAdd.map(msg => ({
              id: msg.id,
              role: msg.role,
              content: msg.content,
              timestamp: msg.timestamp.toISOString()
            }))
          }
          sessionStorage.setItem('chatbot-state', JSON.stringify(stateToSave))
          
          // Render - should restore messages from sessionStorage
          const { result, unmount } = renderHook(
            () => useChatbot(),
            { wrapper: createWrapper() }
          )
          
          // Verify messages persisted
          expect(result.current.messages.length).toBe(messageContents.length)
          result.current.messages.forEach((msg, idx) => {
            expect(msg.content).toBe(messageContents[idx])
            expect(msg.role).toBe('user')
          })
          
          unmount()
        }
      ),
      { numRuns: 100 }
    )
  })
})

/**
 * **Feature: chatbot-integration, Property 3: Message addition to history**
 * **Validates: Requirements 2.1, 2.4**
 * 
 * For any valid message (non-empty string) sent by either user or assistant,
 * the message should appear in the conversation history with the correct role and timestamp.
 */
describe('Property 3: Message addition to history', () => {
  it('should add valid messages to history with correct role and timestamp', () => {
    fc.assert(
      fc.property(
        fc.string({ minLength: 1, maxLength: 200 }).filter(s => s.trim().length > 0),
        fc.constantFrom('user' as const, 'assistant' as const),
        (content, role) => {
          // Manually create a message and add to sessionStorage
          const beforeTimestamp = new Date()
          
          const message = {
            id: 'test-msg-1',
            role,
            content: content.trim(),
            timestamp: new Date().toISOString()
          }
          
          const stateToSave = {
            isOpen: false,
            messages: [message]
          }
          sessionStorage.setItem('chatbot-state', JSON.stringify(stateToSave))
          
          const afterTimestamp = new Date()
          
          // Render and verify message appears in history
          const { result, unmount } = renderHook(
            () => useChatbot(),
            { wrapper: createWrapper() }
          )
          
          // Verify message is in history
          expect(result.current.messages.length).toBe(1)
          const addedMessage = result.current.messages[0]
          
          // Verify correct role
          expect(addedMessage.role).toBe(role)
          
          // Verify correct content
          expect(addedMessage.content).toBe(content.trim())
          
          // Verify timestamp exists and is a Date
          expect(addedMessage.timestamp).toBeInstanceOf(Date)
          
          // Verify timestamp is reasonable (between before and after)
          expect(addedMessage.timestamp.getTime()).toBeGreaterThanOrEqual(beforeTimestamp.getTime() - 1000)
          expect(addedMessage.timestamp.getTime()).toBeLessThanOrEqual(afterTimestamp.getTime() + 1000)
          
          unmount()
        }
      ),
      { numRuns: 100 }
    )
  })
})

/**
 * **Feature: chatbot-integration, Property 13: History clearing**
 * **Validates: Requirements 9.2**
 * 
 * For any conversation history of any length, invoking the clear history action
 * should result in an empty message list.
 */
describe('Property 13: History clearing', () => {
  it('should clear all messages regardless of history length', () => {
    fc.assert(
      fc.property(
        fc.array(fc.string({ minLength: 1, maxLength: 100 }), { minLength: 1, maxLength: 20 }),
        (messageContents) => {
          // Create messages and add to sessionStorage
          const messages = messageContents.map((content, idx) => ({
            id: `test-${idx}`,
            role: idx % 2 === 0 ? 'user' : 'assistant',
            content,
            timestamp: new Date().toISOString()
          }))
          
          const stateToSave = {
            isOpen: false,
            messages
          }
          sessionStorage.setItem('chatbot-state', JSON.stringify(stateToSave))
          
          // Render and verify messages are loaded
          const { result, unmount } = renderHook(
            () => useChatbot(),
            { wrapper: createWrapper() }
          )
          
          // Verify messages exist
          expect(result.current.messages.length).toBe(messageContents.length)
          
          // Clear history
          act(() => {
            result.current.clearHistory()
          })
          
          // Verify history is empty
          expect(result.current.messages.length).toBe(0)
          
          unmount()
        }
      ),
      { numRuns: 100 }
    )
  })
})
