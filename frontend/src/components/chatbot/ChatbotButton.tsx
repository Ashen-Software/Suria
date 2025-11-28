/**
 * ChatbotButton Component
 * 
 * Floating button that toggles the chatbot window open/closed.
 * Positioned at bottom-right of the screen with fixed positioning.
 * Styled with TailwindCSS and DaisyUI for consistency with app design.
 */

import { useChatbot } from '@/contexts/ChatbotContext'

/**
 * ChatbotButton Props
 */
interface ChatbotButtonProps {
  /** Optional notification badge count for unread messages */
  unreadCount?: number
}

/**
 * ChatbotButton Component
 * 
 * Displays a floating button in the bottom-right corner that opens the chatbot.
 * Shows an optional notification badge when there are unread messages.
 */
export function ChatbotButton({ unreadCount = 0 }: ChatbotButtonProps) {
  const { toggleOpen } = useChatbot()
  
  return (
    <button
      onClick={toggleOpen}
      className="btn btn-circle btn-primary btn-lg fixed bottom-6 right-6 z-50 shadow-2xl transition-all duration-300 hover:scale-110 hover:shadow-primary/50"
      aria-label="Abrir asistente virtual"
      title="Asistente Virtual"
    >
      {/* Chat icon */}
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
          d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z"
        />
      </svg>
      
      {/* Optional notification badge */}
      {unreadCount > 0 && (
        <span className="badge badge-error badge-sm absolute -right-1 -top-1 animate-pulse">
          {unreadCount > 9 ? '9+' : unreadCount}
        </span>
      )}
    </button>
  )
}
