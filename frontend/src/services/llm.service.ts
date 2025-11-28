/**
 * LLM Service
 * 
 * Service layer for integrating with OpenAI API to generate chatbot responses.
 * Handles system prompt construction, message formatting, and error handling.
 */

import type { Message, ChatContext, LLMConfig, ChatError } from '../types/chatbot.types'

/**
 * OpenAI API response structure
 */
interface OpenAIMessage {
  role: 'system' | 'user' | 'assistant'
  content: string
}

interface OpenAIResponse {
  choices: Array<{
    message: {
      content: string
    }
  }>
}

/**
 * LLM Service class for OpenAI integration
 */
export class LLMService {
  private config: LLMConfig

  constructor(config?: Partial<LLMConfig>) {
    // Load configuration from environment variables with defaults
    this.config = {
      provider: 'openai',
      apiKey: import.meta.env.VITE_OPENAI_API_KEY || '',
      model: import.meta.env.VITE_OPENAI_MODEL || 'gpt-4-turbo',
      temperature: parseFloat(import.meta.env.VITE_CHATBOT_TEMPERATURE || '0.7'),
      maxTokens: parseInt(import.meta.env.VITE_CHATBOT_MAX_TOKENS || '1000', 10),
      systemPrompt: '', // Will be built dynamically
      ...config
    }

    if (!this.config.apiKey) {
      console.warn('OpenAI API key not configured. Set VITE_OPENAI_API_KEY in environment.')
    }
  }

  /**
   * Build system prompt with application context
   * 
   * @param context - Current application context
   * @returns System prompt string
   */
  buildSystemPrompt(context: ChatContext): string {
    const availableDataStr = context.availableData
      ? Object.entries(context.availableData)
          .filter(([_, available]) => available)
          .map(([key]) => key)
          .join(', ')
      : 'ninguno'

    return `Eres un asistente virtual para una aplicación de gestión de datos llamada "${context.appInfo.name}".

INFORMACIÓN DE LA APLICACIÓN:
- Aplicación React + TypeScript para visualización y gestión de datos
- Usa Supabase como backend
- Tiene las siguientes páginas:
  * Home (/) - Página principal
  * ETL Sources (/etl) - Gestión de fuentes de datos ETL
  * Dimensión Tiempo (/tiempo) - Tabla de dimensión temporal
  * Dimensión Territorios (/territorios) - Tabla de dimensión geográfica
  * UPME (/upme) - Datos de UPME

TABLAS DE DATOS:
1. dim_territorios: Contiene información geográfica (códigos, nombres, jerarquías)
2. dim_tiempo: Contiene información temporal (fechas, períodos, años)
3. etl_sources: Contiene configuración de fuentes de datos ETL

CONTEXTO ACTUAL:
- Página actual: ${context.currentRoute} (${context.routeName})
- Datos disponibles: ${availableDataStr}

INSTRUCCIONES:
- Responde SIEMPRE en español
- Sé conciso y claro
- Proporciona ejemplos cuando sea útil
- Si no sabes algo, admítelo
- Ayuda con navegación, explicación de datos y funcionalidades`
  }

  /**
   * Send message to LLM and get response
   * 
   * @param messages - Conversation history
   * @param context - Current application context
   * @returns Assistant response content
   * @throws ChatError on failure
   */
  async sendMessage(messages: Message[], context: ChatContext): Promise<string> {
    // Validate API key
    if (!this.config.apiKey) {
      throw this.createError(
        'validation',
        'API key not configured',
        'El servicio de chat no está configurado correctamente.',
        false
      )
    }

    // Build system prompt
    const systemPrompt = this.buildSystemPrompt(context)

    // Format messages for OpenAI API
    const openAIMessages: OpenAIMessage[] = [
      { role: 'system', content: systemPrompt },
      ...messages.map(msg => ({
        role: msg.role as 'user' | 'assistant',
        content: msg.content
      }))
    ]

    // Attempt to send with retry logic
    return await this.sendWithRetry(openAIMessages)
  }

  /**
   * Send request with retry logic for transient failures
   */
  private async sendWithRetry(
    messages: OpenAIMessage[],
    maxRetries: number = 2
  ): Promise<string> {
    let lastError: ChatError | null = null

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await this.callOpenAI(messages)
      } catch (error) {
        lastError = this.handleError(error)

        // Only retry if error is retryable and we have attempts left
        if (!lastError.retryable || attempt === maxRetries) {
          throw lastError
        }

        // Wait before retrying (exponential backoff)
        await this.delay(Math.pow(2, attempt) * 1000)
      }
    }

    // Should never reach here, but TypeScript needs this
    throw lastError!
  }

  /**
   * Call OpenAI API
   */
  private async callOpenAI(messages: OpenAIMessage[]): Promise<string> {
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.config.apiKey}`
      },
      body: JSON.stringify({
        model: this.config.model,
        messages,
        temperature: this.config.temperature,
        max_tokens: this.config.maxTokens
      })
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      
      // Handle specific error codes
      if (response.status === 429) {
        throw this.createError(
          'api',
          `Rate limit exceeded: ${JSON.stringify(errorData)}`,
          'Has alcanzado el límite de mensajes. Por favor, espera un momento antes de continuar.',
          true
        )
      }

      if (response.status === 401) {
        throw this.createError(
          'api',
          'Invalid API key',
          'La configuración del servicio es inválida. Por favor, contacta al administrador.',
          false
        )
      }

      if (response.status >= 500) {
        throw this.createError(
          'api',
          `Server error: ${response.status}`,
          'El servicio está temporalmente no disponible. Por favor, intenta de nuevo en unos momentos.',
          true
        )
      }

      throw this.createError(
        'api',
        `API error: ${response.status} - ${JSON.stringify(errorData)}`,
        'Ocurrió un error al procesar tu mensaje. Por favor, intenta de nuevo.',
        false
      )
    }

    const data: OpenAIResponse = await response.json()

    if (!data.choices || data.choices.length === 0) {
      throw this.createError(
        'api',
        'No response from API',
        'No se recibió respuesta del servicio. Por favor, intenta de nuevo.',
        true
      )
    }

    return data.choices[0].message.content
  }

  /**
   * Handle errors and convert to ChatError
   */
  private handleError(error: unknown): ChatError {
    // If already a ChatError, return it
    if (this.isChatError(error)) {
      return error
    }

    // Network errors
    if (error instanceof TypeError && error.message.includes('fetch')) {
      return this.createError(
        'network',
        error.message,
        'No se pudo conectar con el servicio. Por favor, verifica tu conexión a internet.',
        true
      )
    }

    // Unknown errors
    return this.createError(
      'unknown',
      error instanceof Error ? error.message : String(error),
      'Ocurrió un error inesperado. Por favor, intenta de nuevo.',
      true
    )
  }

  /**
   * Create a ChatError object
   */
  private createError(
    type: ChatError['type'],
    message: string,
    userMessage: string,
    retryable: boolean
  ): ChatError {
    return { type, message, userMessage, retryable }
  }

  /**
   * Type guard for ChatError
   */
  private isChatError(value: unknown): value is ChatError {
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

  /**
   * Delay helper for retry logic
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }
}

/**
 * Create a default LLM service instance
 */
export function createLLMService(config?: Partial<LLMConfig>): LLMService {
  return new LLMService(config)
}
