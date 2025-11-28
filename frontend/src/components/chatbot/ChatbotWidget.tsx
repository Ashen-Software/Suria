/**
 * ChatbotWidget Component
 * 
 * Main chatbot widget that integrates ChatbotButton and ChatbotWindow.
 * Features:
 * - Conditional rendering based on open/closed state
 * - Keyboard shortcuts (Escape to close)
 * - Connected to ChatbotContext for state management
 * 
 * Requirements: 1.1, 1.2, 1.3
 */

import { useEffect } from 'react'
import { useChatbot } from '@/contexts/ChatbotContext'
import { ChatbotButton } from './ChatbotButton'
import { ChatbotWindow } from './ChatbotWindow'

/**
 * ChatbotWidget Component
 * 
 * Main component that orchestrates the chatbot UI.
 * Renders either the floating button (collapsed) or the full window (expanded).
 * Handles keyboard shortcuts for accessibility.
 */
export function ChatbotWidget() {
  const { isOpen, toggleOpen } = useChatbot()
  
  /**
   * Handle keyboard shortcuts
   * - Escape: Close the chatbot if open
   */
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Close chatbot on Escape key
      if (event.key === 'Escape' && isOpen) {
        event.preventDefault()
        toggleOpen()
      }
    }
    
    // Add event listener
    window.addEventListener('keydown', handleKeyDown)
    
    // Cleanup
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [isOpen, toggleOpen])
  
  return (
    <>
      {/* Floating button - shown when chatbot is closed */}
      {!isOpen && <ChatbotButton />}
      
      {/* Chat window - shown when chatbot is open */}
      <ChatbotWindow />
    </>
  )
}
