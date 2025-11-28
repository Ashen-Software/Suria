/**
 * Chatbot Domain Types
 * 
 * This file contains all TypeScript interfaces and types for the chatbot feature.
 * These types align with the design document specifications.
 */

/**
 * Message role types
 */
export type MessageRole = 'user' | 'assistant' | 'system'

/**
 * Message interface representing a single chat message
 */
export interface Message {
  id: string              // UUID generated
  role: MessageRole       // Role of the message sender
  content: string         // Message content
  timestamp: Date         // Creation timestamp
}

/**
 * Chat context containing application state information
 */
export interface ChatContext {
  // Navigation information
  currentRoute: string    // e.g., '/territorios'
  routeName: string       // e.g., 'Territorios'
  
  // Available data information
  availableData?: {
    territorios?: boolean
    tiempo?: boolean
    etlSources?: boolean
  }
  
  // Application metadata
  appInfo: {
    name: string
    version: string
    description: string
  }
}

/**
 * LLM provider types
 */
export type LLMProvider = 'openai' | 'anthropic'

/**
 * LLM configuration interface
 */
export interface LLMConfig {
  provider: LLMProvider   // LLM provider
  apiKey: string          // API key from environment
  model: string           // Specific model to use
  temperature: number     // 0-1, response creativity
  maxTokens: number       // Token limit
  systemPrompt: string    // Base system prompt
}

/**
 * Chat error types
 */
export type ChatErrorType = 'network' | 'api' | 'validation' | 'unknown'

/**
 * Chat error interface
 */
export interface ChatError {
  type: ChatErrorType
  message: string         // Technical error message
  userMessage: string     // User-friendly message in Spanish
  retryable: boolean      // Whether the error can be retried
}

/**
 * Chatbot widget state
 */
export interface ChatbotState {
  isOpen: boolean
  messages: Message[]
  isLoading: boolean
}

/**
 * Chatbot widget props
 */
export interface ChatbotWidgetProps {
  position?: 'bottom-right' | 'bottom-left'
  defaultOpen?: boolean
}

/**
 * Chatbot context value for React Context
 */
export interface ChatbotContextValue {
  messages: Message[]
  isLoading: boolean
  isOpen: boolean
  sendMessage: (content: string) => Promise<void>
  clearHistory: () => void
  toggleOpen: () => void
  getContext: () => ChatContext
}

/**
 * LLM Service interface
 */
export interface LLMService {
  sendMessage(messages: Message[], context: ChatContext): Promise<string>
  buildSystemPrompt(context: ChatContext): string
}

/**
 * Route constants mapping paths to route names
 */
export const ROUTE_NAMES: Record<string, string> = {
  '/': 'Home',
  '/etl': 'ETL Sources',
  '/tiempo': 'Dimensión Tiempo',
  '/territorios': 'Dimensión Territorios',
  '/upme': 'UPME'
} as const

/**
 * Data availability mapping for each route
 */
export const ROUTE_DATA_AVAILABILITY: Record<string, ChatContext['availableData']> = {
  '/': {},
  '/etl': { etlSources: true },
  '/tiempo': { tiempo: true },
  '/territorios': { territorios: true },
  '/upme': {}
} as const

/**
 * Type guard to check if a value is a valid MessageRole
 */
export function isMessageRole(value: unknown): value is MessageRole {
  return typeof value === 'string' && ['user', 'assistant', 'system'].includes(value)
}

/**
 * Type guard to check if a value is a valid Message
 */
export function isMessage(value: unknown): value is Message {
  if (typeof value !== 'object' || value === null) {
    return false
  }
  
  const msg = value as Record<string, unknown>
  
  return (
    typeof msg.id === 'string' &&
    isMessageRole(msg.role) &&
    typeof msg.content === 'string' &&
    msg.timestamp instanceof Date
  )
}

/**
 * Validates if a message content is valid (non-empty, not just whitespace)
 */
export function isValidMessageContent(content: string): boolean {
  return typeof content === 'string' && content.trim().length > 0
}

/**
 * Type guard to check if a value is a valid ChatError
 */
export function isChatError(value: unknown): value is ChatError {
  if (typeof value !== 'object' || value === null) {
    return false
  }
  
  const err = value as Record<string, unknown>
  
  return (
    typeof err.type === 'string' &&
    ['network', 'api', 'validation', 'unknown'].includes(err.type) &&
    typeof err.message === 'string' &&
    typeof err.userMessage === 'string' &&
    typeof err.retryable === 'boolean'
  )
}
