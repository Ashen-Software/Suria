/**
 * ChatMessages Component
 * 
 * Scrollable message list container that displays conversation history.
 * Features:
 * - Auto-scroll to bottom on new messages
 * - Loading indicator during message processing
 * - Empty state with suggested questions
 * - Displays all messages in chronological order
 */

import { useEffect, useRef } from 'react'
import type { Message } from '@/types/chatbot.types'
import { ChatMessage } from './ChatMessage'

/**
 * ChatMessages Props
 */
interface ChatMessagesProps {
  messages: Message[]
  isLoading: boolean
  onSuggestedQuestion?: (question: string) => void
}

/**
 * Suggested questions for empty state
 */
const SUGGESTED_QUESTIONS = [
  '¿Qué páginas están disponibles en la aplicación?',
  '¿Cómo puedo navegar a la página de territorios?',
  '¿Qué información contiene la tabla dim_tiempo?',
  '¿Qué funcionalidades tiene esta aplicación?'
]

/**
 * ChatMessages Component
 * 
 * Renders the message list with auto-scroll behavior and empty state.
 */
export function ChatMessages({ messages, isLoading, onSuggestedQuestion }: ChatMessagesProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  
  /**
   * Auto-scroll to bottom when new messages arrive
   */
  useEffect(() => {
    if (messagesEndRef.current && messagesEndRef.current.scrollIntoView) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, isLoading])
  
  /**
   * Handle suggested question click
   */
  const handleSuggestedClick = (question: string) => {
    if (onSuggestedQuestion) {
      onSuggestedQuestion(question)
    }
  }
  
  // Show empty state when no messages
  if (messages.length === 0 && !isLoading) {
    return (
      <div
        className="flex h-full flex-col items-center justify-center p-6 text-center"
        data-testid="empty-state"
      >
        <div className="mb-4">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
            className="mx-auto h-16 w-16 text-base-content/30"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z"
            />
          </svg>
        </div>
        
        <h3 className="mb-2 text-lg font-semibold">¡Hola! Soy tu Asistente Virtual</h3>
        <p className="mb-6 text-sm text-base-content/70">
          Puedo ayudarte con información sobre la aplicación, navegación y datos.
        </p>
        
        <div className="w-full max-w-sm space-y-2">
          <p className="mb-3 text-xs font-medium text-base-content/60">
            Preguntas sugeridas:
          </p>
          {SUGGESTED_QUESTIONS.map((question, index) => (
            <button
              key={index}
              onClick={() => handleSuggestedClick(question)}
              className="btn btn-outline btn-sm w-full justify-start text-left text-xs normal-case"
              data-testid={`suggested-question-${index}`}
            >
              {question}
            </button>
          ))}
        </div>
      </div>
    )
  }
  
  // Show message list
  return (
    <div
      ref={containerRef}
      className="flex h-full flex-col overflow-y-auto p-4"
      data-testid="messages-container"
    >
      {/* Render all messages */}
      {messages.map((message) => (
        <ChatMessage key={message.id} message={message} />
      ))}
      
      {/* Loading indicator */}
      {isLoading && (
        <div className="chat chat-start" data-testid="loading-indicator">
          <div className="chat-image avatar">
            <div className="w-10 rounded-full bg-secondary">
              <div className="flex h-full w-full items-center justify-center text-white">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={2}
                  stroke="currentColor"
                  className="h-6 w-6"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z"
                  />
                </svg>
              </div>
            </div>
          </div>
          <div className="chat-bubble chat-bubble-secondary">
            <span className="loading loading-dots loading-sm"></span>
          </div>
        </div>
      )}
      
      {/* Scroll anchor */}
      <div ref={messagesEndRef} />
    </div>
  )
}
