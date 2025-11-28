/**
 * ChatMessage Component
 * 
 * Renders individual chat messages with role-based styling.
 * Supports markdown rendering for assistant messages.
 * Displays timestamps and differentiates between user and assistant with avatars.
 */

/**
 * ChatMessage Component
 *
 * Renders individual chat messages with role-based styling.
 * Displays timestamps and differentiates between user and assistant with avatars.
 */
import type { Message } from '@/types/chatbot.types'
import ReactMarkdown from 'react-markdown'

/**
 * ChatMessage Props
 */
interface ChatMessageProps {
  message: Message
}

/**
 * Format timestamp to readable format
 */
function formatTimestamp(date: Date): string {
  // Handle invalid dates
  if (isNaN(date.getTime())) {
    return 'Ahora'
  }
  
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  
  if (seconds < 60) {
    return 'Ahora'
  } else if (minutes < 60) {
    return `Hace ${minutes}m`
  } else if (hours < 24) {
    return `Hace ${hours}h`
  } else {
    return date.toLocaleDateString('es-ES', { 
      day: 'numeric', 
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    })
  }
}

/**
 * ChatMessage Component
 * 
 * Renders a single message with appropriate styling based on role.
 * Assistant messages support markdown rendering.
 */
export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'
  const isAssistant = message.role === 'assistant'
  
  // Don't render system messages
  if (message.role === 'system') {
    return null
  }
  
  return (
    <div
      className={`chat ${isUser ? 'chat-end' : 'chat-start'}`}
      data-testid={`message-${message.role}`}
    >
      {/* Avatar */}
      <div className="chat-image avatar">
        <div className={`w-10 rounded-full ${isUser ? 'bg-primary' : 'bg-secondary'}`}>
          <div className="flex h-full w-full items-center justify-center text-white">
            {isUser ? (
              // User icon
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
                  d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z"
                />
              </svg>
            ) : (
              // Assistant icon
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
            )}
          </div>
        </div>
      </div>
      
      {/* Message bubble */}
      <div
        className={`chat-bubble ${
          isUser ? 'chat-bubble-primary' : 'chat-bubble-secondary'
        } max-w-xs break-words whitespace-pre-wrap`}
        data-testid="message-content"
      >
        {isAssistant ? (
          <div className="prose prose-sm max-w-none prose-p:my-2 prose-ul:my-2 prose-ol:my-2 prose-li:my-0">
            <ReactMarkdown
              components={{
                // Customize link rendering to open in new tab
                a: ({ node, ...props }) => (
                  <a {...props} target="_blank" rel="noopener noreferrer" />
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        ) : (
          <span>{message.content}</span>
        )}
      </div>
      
      {/* Timestamp */}
      <div className="chat-footer opacity-50">
        <time className="text-xs" dateTime={message.timestamp.toISOString()}>
          {formatTimestamp(message.timestamp)}
        </time>
      </div>
    </div>
  )
}
