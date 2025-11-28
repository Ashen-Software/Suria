/**
 * ChatInput Component
 * 
 * Input field for sending messages to the chatbot.
 * Features auto-resize textarea, send button, input validation,
 * and automatic clearing after successful send.
 */

import { useState, useRef, useEffect } from 'react'
import type { KeyboardEvent } from 'react'
import { useChatbot } from '@/contexts/ChatbotContext'
import { isValidMessageContent } from '@/types/chatbot.types'

/**
 * ChatInput Component
 * 
 * Provides a textarea with auto-resize functionality and a send button.
 * Validates input to prevent empty messages and disables during processing.
 */
export function ChatInput() {
  const { sendMessage, isLoading } = useChatbot()
  const [input, setInput] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  
  /**
   * Auto-resize textarea based on content
   */
  useEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      // Reset height to auto to get the correct scrollHeight
      textarea.style.height = 'auto'
      // Set height to scrollHeight (content height)
      textarea.style.height = `${textarea.scrollHeight}px`
    }
  }, [input])
  
  /**
   * Handle sending a message
   */
  const handleSend = async () => {
    // Validate message content
    if (!isValidMessageContent(input)) {
      return
    }
    
    // Store the message to send
    const messageToSend = input
    
    // Clear input field immediately
    setInput('')
    
    // Send message
    await sendMessage(messageToSend)
  }
  
  /**
   * Handle Enter key press (send message)
   * Shift+Enter adds a new line
   */
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }
  
  return (
    <div className="border-t border-base-300 bg-base-100 p-4">
      <div className="flex gap-2">
        {/* Textarea input */}
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Escribe tu mensaje..."
          disabled={isLoading}
          className="textarea textarea-bordered flex-1 resize-none overflow-hidden"
          style={{ minHeight: '44px', maxHeight: '120px' }}
          rows={1}
          aria-label="Campo de mensaje"
          data-testid="chat-input"
        />
        
        {/* Send button */}
        <button
          onClick={handleSend}
          disabled={isLoading || !isValidMessageContent(input)}
          className="btn btn-primary btn-square"
          aria-label="Enviar mensaje"
          data-testid="send-button"
        >
          {isLoading ? (
            // Loading spinner
            <span className="loading loading-spinner loading-sm"></span>
          ) : (
            // Send icon
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
              className="h-5 w-5"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5"
              />
            </svg>
          )}
        </button>
      </div>
    </div>
  )
}
