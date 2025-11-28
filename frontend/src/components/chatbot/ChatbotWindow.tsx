/**
 * ChatbotWindow Component
 * 
 * Main chatbot window that composes ChatHeader, ChatMessages, and ChatInput.
 * Features:
 * - Responsive sizing (min 350px, max 450px width)
 * - Slide-in/slide-out animation
 * - Fixed positioning at bottom-right
 * - Shadow and border styling
 */

import { useChatbot } from '@/contexts/ChatbotContext'
import { ChatHeader } from './ChatHeader'
import { ChatMessages } from './ChatMessages'
import { ChatInput } from './ChatInput'

/**
 * ChatbotWindow Component
 * 
 * Renders the expanded chatbot window with all sub-components.
 * Positioned fixed at bottom-right with slide-in animation.
 */
export function ChatbotWindow() {
  const { isOpen, messages, isLoading, sendMessage } = useChatbot()
  
  /**
   * Handle suggested question click from empty state
   */
  const handleSuggestedQuestion = (question: string) => {
    sendMessage(question)
  }
  
  return (
    <div
      className={`fixed bottom-6 right-6 z-50 flex h-[600px] w-full max-w-[450px] min-w-[350px] flex-col overflow-hidden rounded-lg border border-base-300 bg-base-100 shadow-2xl transition-all duration-300 ${
        isOpen
          ? 'translate-x-0 opacity-100'
          : 'pointer-events-none translate-x-[calc(100%+2rem)] opacity-0'
      }`}
      data-testid="chatbot-window"
      aria-hidden={!isOpen}
    >
      {/* Header */}
      <ChatHeader />
      
      {/* Messages container - takes remaining space */}
      <div className="flex-1 overflow-hidden">
        <ChatMessages
          messages={messages}
          isLoading={isLoading}
          onSuggestedQuestion={handleSuggestedQuestion}
        />
      </div>
      
      {/* Input */}
      <ChatInput />
    </div>
  )
}
