/**
 * LLM Service Tests
 * 
 * Property-based and unit tests for the LLM service layer.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import * as fc from 'fast-check'
import { LLMService } from './llm.service'
import type { Message, ChatContext } from '../types/chatbot.types'

// Declare global for TypeScript
declare const global: typeof globalThis

// Mock fetch globally
const originalFetch = global.fetch

describe('LLMService', () => {
  beforeEach(() => {
    // Reset fetch mock before each test
    global.fetch = vi.fn()
  })

  afterEach(() => {
    // Restore original fetch
    global.fetch = originalFetch
    vi.restoreAllMocks()
  })

  describe('Property 10: LLM request includes system prompt and history', () => {
    /**
     * **Feature: chatbot-integration, Property 10: LLM request includes system prompt and history**
     * **Validates: Requirements 7.2, 7.3**
     * 
     * For any request sent to the LLM service, the request should include both 
     * the system prompt with application context and the recent conversation history.
     */
    it('should include system prompt and message history in all requests', async () => {
      await fc.assert(
        fc.asyncProperty(
          // Generate arbitrary message history
          fc.array(
            fc.record({
              id: fc.uuid(),
              role: fc.constantFrom('user' as const, 'assistant' as const),
              content: fc.string({ minLength: 1, maxLength: 200 }),
              timestamp: fc.date()
            }),
            { minLength: 0, maxLength: 10 }
          ),
          // Generate arbitrary context
          fc.record({
            currentRoute: fc.constantFrom('/', '/etl', '/tiempo', '/territorios', '/upme'),
            routeName: fc.constantFrom('Home', 'ETL Sources', 'Dimensión Tiempo', 'Dimensión Territorios', 'UPME'),
            availableData: fc.record({
              territorios: fc.boolean(),
              tiempo: fc.boolean(),
              etlSources: fc.boolean()
            }),
            appInfo: fc.record({
              name: fc.constant('Datos 2025'),
              version: fc.constant('1.0.0'),
              description: fc.constant('Aplicación de gestión de datos')
            })
          }),
          async (messages: Message[], context: ChatContext) => {
            // Mock successful API response
            const mockFetch = vi.fn().mockResolvedValue({
              ok: true,
              json: async () => ({
                choices: [
                  {
                    message: {
                      content: 'Test response'
                    }
                  }
                ]
              })
            })
            global.fetch = mockFetch

            const service = new LLMService({
              apiKey: 'test-api-key'
            })

            // Send message
            await service.sendMessage(messages, context)

            // Verify fetch was called
            expect(mockFetch).toHaveBeenCalledTimes(1)

            // Get the request body
            const callArgs = mockFetch.mock.calls[0]
            const requestBody = JSON.parse(callArgs[1].body as string)

            // Property: Request must include messages array
            expect(requestBody.messages).toBeDefined()
            expect(Array.isArray(requestBody.messages)).toBe(true)

            // Property: First message must be system prompt
            expect(requestBody.messages.length).toBeGreaterThan(0)
            expect(requestBody.messages[0].role).toBe('system')
            expect(requestBody.messages[0].content).toBeDefined()
            expect(typeof requestBody.messages[0].content).toBe('string')
            expect(requestBody.messages[0].content.length).toBeGreaterThan(0)

            // Property: System prompt must include context information
            const systemPrompt = requestBody.messages[0].content
            expect(systemPrompt).toContain(context.currentRoute)
            expect(systemPrompt).toContain(context.routeName)
            expect(systemPrompt).toContain(context.appInfo.name)

            // Property: All conversation messages must be included after system prompt
            expect(requestBody.messages.length).toBe(messages.length + 1) // +1 for system prompt
            
            // Verify each message from history is included
            messages.forEach((msg, index) => {
              const requestMsg = requestBody.messages[index + 1] // +1 to skip system prompt
              expect(requestMsg.role).toBe(msg.role)
              expect(requestMsg.content).toBe(msg.content)
            })
          }
        ),
        { numRuns: 100 }
      )
    })
  })

  describe('buildSystemPrompt', () => {
    it('should build system prompt with context information', () => {
      const service = new LLMService({ apiKey: 'test-key' })
      
      const context: ChatContext = {
        currentRoute: '/territorios',
        routeName: 'Dimensión Territorios',
        availableData: {
          territorios: true,
          tiempo: false,
          etlSources: false
        },
        appInfo: {
          name: 'Datos 2025',
          version: '1.0.0',
          description: 'Test app'
        }
      }

      const prompt = service.buildSystemPrompt(context)

      // Verify prompt contains key information
      expect(prompt).toContain('Datos 2025')
      expect(prompt).toContain('/territorios')
      expect(prompt).toContain('Dimensión Territorios')
      expect(prompt).toContain('territorios')
      expect(prompt).toContain('español')
    })
  })

  describe('Error Handling', () => {
    /**
     * Unit tests for LLM service error handling
     * Tests network errors, API errors, and rate limiting
     * **Validates: Requirements 7.4**
     */

    it('should handle network errors', async () => {
      // Mock network failure
      const mockFetch = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'))
      global.fetch = mockFetch

      const service = new LLMService({ apiKey: 'test-key' })
      const context: ChatContext = {
        currentRoute: '/',
        routeName: 'Home',
        appInfo: {
          name: 'Test App',
          version: '1.0.0',
          description: 'Test'
        }
      }

      await expect(service.sendMessage([], context)).rejects.toMatchObject({
        type: 'network',
        userMessage: 'No se pudo conectar con el servicio. Por favor, verifica tu conexión a internet.',
        retryable: true
      })
    })

    it('should handle API rate limiting (429)', async () => {
      // Mock rate limit response
      const mockFetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 429,
        json: async () => ({ error: 'Rate limit exceeded' })
      })
      global.fetch = mockFetch

      const service = new LLMService({ apiKey: 'test-key' })
      const context: ChatContext = {
        currentRoute: '/',
        routeName: 'Home',
        appInfo: {
          name: 'Test App',
          version: '1.0.0',
          description: 'Test'
        }
      }

      await expect(service.sendMessage([], context)).rejects.toMatchObject({
        type: 'api',
        userMessage: 'Has alcanzado el límite de mensajes. Por favor, espera un momento antes de continuar.',
        retryable: true
      })
    })

    it('should handle invalid API key (401)', async () => {
      // Mock unauthorized response
      const mockFetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        json: async () => ({ error: 'Invalid API key' })
      })
      global.fetch = mockFetch

      const service = new LLMService({ apiKey: 'invalid-key' })
      const context: ChatContext = {
        currentRoute: '/',
        routeName: 'Home',
        appInfo: {
          name: 'Test App',
          version: '1.0.0',
          description: 'Test'
        }
      }

      await expect(service.sendMessage([], context)).rejects.toMatchObject({
        type: 'api',
        userMessage: 'La configuración del servicio es inválida. Por favor, contacta al administrador.',
        retryable: false
      })
    })

    it('should handle server errors (500+)', async () => {
      // Mock server error response
      const mockFetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
        json: async () => ({ error: 'Service unavailable' })
      })
      global.fetch = mockFetch

      const service = new LLMService({ apiKey: 'test-key' })
      const context: ChatContext = {
        currentRoute: '/',
        routeName: 'Home',
        appInfo: {
          name: 'Test App',
          version: '1.0.0',
          description: 'Test'
        }
      }

      await expect(service.sendMessage([], context)).rejects.toMatchObject({
        type: 'api',
        userMessage: 'El servicio está temporalmente no disponible. Por favor, intenta de nuevo en unos momentos.',
        retryable: true
      })
    })

    it('should handle missing API key', async () => {
      const service = new LLMService({ apiKey: '' })
      const context: ChatContext = {
        currentRoute: '/',
        routeName: 'Home',
        appInfo: {
          name: 'Test App',
          version: '1.0.0',
          description: 'Test'
        }
      }

      await expect(service.sendMessage([], context)).rejects.toMatchObject({
        type: 'validation',
        userMessage: 'El servicio de chat no está configurado correctamente.',
        retryable: false
      })
    })

    it('should handle empty API response', async () => {
      // Mock empty response
      const mockFetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ choices: [] })
      })
      global.fetch = mockFetch

      const service = new LLMService({ apiKey: 'test-key' })
      const context: ChatContext = {
        currentRoute: '/',
        routeName: 'Home',
        appInfo: {
          name: 'Test App',
          version: '1.0.0',
          description: 'Test'
        }
      }

      await expect(service.sendMessage([], context)).rejects.toMatchObject({
        type: 'api',
        userMessage: 'No se recibió respuesta del servicio. Por favor, intenta de nuevo.',
        retryable: true
      })
    })

    it('should retry on retryable errors', async () => {
      // Mock fetch to fail twice then succeed
      let callCount = 0
      const mockFetch = vi.fn().mockImplementation(() => {
        callCount++
        if (callCount <= 2) {
          return Promise.resolve({
            ok: false,
            status: 503,
            json: async () => ({ error: 'Service unavailable' })
          })
        }
        return Promise.resolve({
          ok: true,
          json: async () => ({
            choices: [{ message: { content: 'Success after retry' } }]
          })
        })
      })
      global.fetch = mockFetch

      const service = new LLMService({ apiKey: 'test-key' })
      const context: ChatContext = {
        currentRoute: '/',
        routeName: 'Home',
        appInfo: {
          name: 'Test App',
          version: '1.0.0',
          description: 'Test'
        }
      }

      const response = await service.sendMessage([], context)
      
      // Should have retried and eventually succeeded
      expect(response).toBe('Success after retry')
      expect(mockFetch).toHaveBeenCalledTimes(3)
    })

    it('should not retry on non-retryable errors', async () => {
      // Mock fetch to return 401 (non-retryable)
      const mockFetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        json: async () => ({ error: 'Invalid API key' })
      })
      global.fetch = mockFetch

      const service = new LLMService({ apiKey: 'invalid-key' })
      const context: ChatContext = {
        currentRoute: '/',
        routeName: 'Home',
        appInfo: {
          name: 'Test App',
          version: '1.0.0',
          description: 'Test'
        }
      }

      await expect(service.sendMessage([], context)).rejects.toMatchObject({
        type: 'api',
        retryable: false
      })

      // Should only be called once (no retries)
      expect(mockFetch).toHaveBeenCalledTimes(1)
    })
  })
})
