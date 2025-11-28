/**
 * Property-Based Tests for Application Context Service
 * 
 * These tests verify the correctness properties defined in the design document
 * using property-based testing with fast-check.
 */

import { describe, test, expect } from 'vitest'
import * as fc from 'fast-check'
import { buildContextFromRoute } from './useAppContext'
import { ROUTE_NAMES, ROUTE_DATA_AVAILABILITY } from '@/types/chatbot.types'

/**
 * Custom generator for valid application routes
 */
const arbitraryValidRoute = () => fc.constantFrom(
  '/',
  '/etl',
  '/tiempo',
  '/territorios',
  '/upme'
)

/**
 * Custom generator for arbitrary path strings (including invalid routes)
 */
const arbitraryPathname = () => fc.oneof(
  arbitraryValidRoute(),
  fc.string().map(s => `/${s}`),
  fc.constant('/unknown-route'),
  fc.constant('/some/nested/path')
)

describe('Application Context Service - Property Tests', () => {
  /**
   * **Feature: chatbot-integration, Property 7: Context includes current route**
   * **Validates: Requirements 3.1**
   * 
   * For any pathname, the context should include the current route path and route name.
   */
  test('Property 7: Context includes current route', () => {
    fc.assert(
      fc.property(arbitraryPathname(), (pathname) => {
        const context = buildContextFromRoute(pathname)
        
        // Context must include the current route
        expect(context.currentRoute).toBe(pathname)
        
        // Context must include a route name (either from mapping or 'Unknown')
        expect(context.routeName).toBeDefined()
        expect(typeof context.routeName).toBe('string')
        expect(context.routeName.length).toBeGreaterThan(0)
        
        // If the route is in our mapping, it should use the mapped name
        if (pathname in ROUTE_NAMES) {
          expect(context.routeName).toBe(ROUTE_NAMES[pathname])
        } else {
          // Otherwise it should default to 'Unknown'
          expect(context.routeName).toBe('Unknown')
        }
      }),
      { numRuns: 100 }
    )
  })

  /**
   * **Feature: chatbot-integration, Property 8: Context includes available data**
   * **Validates: Requirements 3.2**
   * 
   * For any message sent from a data page (territorios, tiempo, or etl),
   * the request context should indicate which data is available on that page.
   */
  test('Property 8: Context includes available data', () => {
    fc.assert(
      fc.property(arbitraryPathname(), (pathname) => {
        const context = buildContextFromRoute(pathname)
        
        // Context must have availableData property
        expect(context.availableData).toBeDefined()
        
        // If the route has data availability mapping, it should match
        if (pathname in ROUTE_DATA_AVAILABILITY) {
          const expectedData = ROUTE_DATA_AVAILABILITY[pathname]
          expect(context.availableData).toEqual(expectedData)
          
          // Verify specific data pages have correct flags
          if (pathname === '/territorios') {
            expect(context.availableData?.territorios).toBe(true)
          }
          if (pathname === '/tiempo') {
            expect(context.availableData?.tiempo).toBe(true)
          }
          if (pathname === '/etl') {
            expect(context.availableData?.etlSources).toBe(true)
          }
        } else {
          // Unknown routes should have empty data availability
          expect(context.availableData).toEqual({})
        }
      }),
      { numRuns: 100 }
    )
  })

  /**
   * Additional property: Context always includes app info
   * This ensures the context is complete for LLM requests
   */
  test('Context always includes complete app info', () => {
    fc.assert(
      fc.property(arbitraryPathname(), (pathname) => {
        const context = buildContextFromRoute(pathname)
        
        // App info must be present and complete
        expect(context.appInfo).toBeDefined()
        expect(context.appInfo.name).toBe('Datos 2025')
        expect(context.appInfo.version).toBeDefined()
        expect(context.appInfo.description).toBeDefined()
        expect(typeof context.appInfo.name).toBe('string')
        expect(typeof context.appInfo.version).toBe('string')
        expect(typeof context.appInfo.description).toBe('string')
      }),
      { numRuns: 100 }
    )
  })
})
