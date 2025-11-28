/**
 * Chatbot Context Provider
 * 
 * Global state management for the chatbot feature using React Context API.
 * Manages messages, loading state, open/closed state, and provides actions
 * for sending messages and clearing history.
 */

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { v4 as uuidv4 } from 'uuid'
import type { Message, ChatbotContextValue, ChatError } from '@/types/chatbot.types'
import { isValidMessageContent } from '@/types/chatbot.types'
import { useAppContext } from '@/hooks/useAppContext'
import { createLLMService } from '@/services/llm.service'

/**
 * Chatbot Context
 */
const ChatbotContext = createContext<ChatbotContextValue | undefined>(undefined)

/**
 * Storage key for persisting chatbot state
 */
const STORAGE_KEY = 'chatbot-state'

/**
 * Persisted state structure
 */
interface PersistedState {
  isOpen: boolean
  messages: Array<{
    id: string
    role: string
    content: string
    timestamp: string
  }>
}

/**
 * ChatbotProvider Props
 */
interface ChatbotProviderProps {
  children: React.ReactNode
}

/**
 * ChatbotProvider Component
 * 
 * Provides chatbot state and actions to all child components.
 * Persists state to sessionStorage to maintain state across navigation.
 */
export function ChatbotProvider({ children }: ChatbotProviderProps) {
  // Initialize LLM service
  const llmService = createLLMService()
  
  // Get current application context
  const appContext = useAppContext()
  
  // Load initial state from sessionStorage
  const loadPersistedState = (): PersistedState | null => {
    try {
      const stored = sessionStorage.getItem(STORAGE_KEY)
      if (stored) {
        const parsed = JSON.parse(stored)
        return parsed
      }
    } catch (error) {
      console.error('Failed to load persisted chatbot state:', error)
    }
    return null
  }
  
  const persistedState = loadPersistedState()
  
  // State management
  const [isOpen, setIsOpen] = useState<boolean>(persistedState?.isOpen ?? false)
  const [messages, setMessages] = useState<Message[]>(() => {
    if (persistedState?.messages) {
      // Convert persisted messages back to Message objects with Date instances
      return persistedState.messages.map(msg => ({
        ...msg,
        timestamp: new Date(msg.timestamp)
      })) as Message[]
    }
    return []
  })
  const [isLoading, setIsLoading] = useState<boolean>(false)
  
  // Persist state to sessionStorage whenever it changes
  useEffect(() => {
    try {
      const stateToSave: PersistedState = {
        isOpen,
        messages: messages.map(msg => ({
          id: msg.id,
          role: msg.role,
          content: msg.content,
          timestamp: msg.timestamp.toISOString()
        }))
      }
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(stateToSave))
    } catch (error) {
      console.error('Failed to persist chatbot state:', error)
    }
  }, [isOpen, messages])
  
  /**
   * Toggle chatbot open/closed state
   */
  const toggleOpen = useCallback(() => {
    setIsOpen(prev => !prev)
  }, [])
  
  /**
   * Send a message to the chatbot
   * 
   * @param content - Message content from user
   */
  const sendMessage = useCallback(async (content: string): Promise<void> => {
    // Validate message content
    if (!isValidMessageContent(content)) {
      console.warn('Attempted to send invalid message:', content)
      return
    }
    
    // Create user message
    const userMessage: Message = {
      id: uuidv4(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date()
    }
    
    // Add user message to history
    setMessages(prev => [...prev, userMessage])
    
    // Set loading state
    setIsLoading(true)
    
    try {
      // Get current context
      const context = appContext
      
      // Send to LLM service with updated message history
      const updatedMessages = [...messages, userMessage]
      const response = await llmService.sendMessage(updatedMessages, context)
      
      // Create assistant message
      const assistantMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: response,
        timestamp: new Date()
      }
      
      // Add assistant message to history
      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Failed to send message:', error)
      
      // Create error message for user
      const errorMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: (error as ChatError).userMessage || 'Ocurrió un error al procesar tu mensaje. Por favor, intenta de nuevo.',
        timestamp: new Date()
      }
      
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }, [messages, appContext, llmService])
  
  /**
   * Clear conversation history
   */
  const clearHistory = useCallback(() => {
    setMessages([])
  }, [])
  
  /**
   * Get current application context
   */
  const getContext = useCallback(() => {
    return appContext
  }, [appContext])
  
  // Context value
  const value: ChatbotContextValue = {
    messages,
    isLoading,
    isOpen,
    sendMessage,
    clearHistory,
    toggleOpen,
    getContext
  }
  
  return (
    <ChatbotContext.Provider value={value}>
      {children}
    </ChatbotContext.Provider>
  )
}

/**
 * Hook to access chatbot context
 * 
 * @returns ChatbotContextValue
 * @throws Error if used outside ChatbotProvider
 */
export function useChatbot(): ChatbotContextValue {
  const context = useContext(ChatbotContext)
  
  if (context === undefined) {
    throw new Error('useChatbot must be used within a ChatbotProvider')
  }
  
  return context
}
