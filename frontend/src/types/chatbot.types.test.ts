/**
 * Property-Based Tests for Chatbot Types
 * 
 * Feature: chatbot-integration
 */

import { describe, it, expect } from 'vitest'
import * as fc from 'fast-check'
import { isValidMessageContent } from './chatbot.types'

describe('Chatbot Types - Property-Based Tests', () => {
  /**
   * Feature: chatbot-integration, Property 6: Empty message rejection
   * Validates: Requirements 2.5
   * 
   * For any string composed entirely of whitespace characters (including empty strings),
   * attempting to send it should be prevented and the message should not appear in the history.
   */
  it('Property 6: Empty message rejection - whitespace-only strings should be invalid', () => {
    fc.assert(
      fc.property(
        // Generate strings composed entirely of whitespace characters
        fc.array(fc.constantFrom(' ', '\t', '\n', '\r'), { minLength: 0, maxLength: 50 }).map(arr => arr.join('')),
        (whitespaceString) => {
          // Validate that whitespace-only strings are rejected
          const result = isValidMessageContent(whitespaceString)
          expect(result).toBe(false)
        }
      ),
      { numRuns: 100 }
    )
  })

  /**
   * Additional test: Valid messages should be accepted
   * This ensures our validation doesn't reject valid messages
   */
  it('Property 6 (inverse): Non-empty messages with content should be valid', () => {
    fc.assert(
      fc.property(
        // Generate strings that contain at least one non-whitespace character
        fc.string({ minLength: 1 }).filter(s => s.trim().length > 0),
        (validMessage) => {
          // Validate that non-empty strings are accepted
          const result = isValidMessageContent(validMessage)
          expect(result).toBe(true)
        }
      ),
      { numRuns: 100 }
    )
  })
})
