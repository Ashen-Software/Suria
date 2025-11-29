/**
 * Application Context Hook
 * 
 * This hook provides the current application context including route information
 * and available data for the chatbot to use when generating responses.
 */

import { useLocation } from 'react-router'
import type { ChatContext } from '@/types/chatbot.types'
import { ROUTE_NAMES, ROUTE_DATA_AVAILABILITY } from '@/types/chatbot.types'

/**
 * Builds a ChatContext object from the current route
 * 
 * @param pathname - The current route pathname (e.g., '/territorios')
 * @returns ChatContext object with route and data availability information
 */
export function buildContextFromRoute(pathname: string): ChatContext {
  // Get route name from mapping, default to 'Unknown' if not found
  const routeName = ROUTE_NAMES[pathname] || 'Unknown'
  
  // Get available data for this route
  const availableData = ROUTE_DATA_AVAILABILITY[pathname] || {}
  
  return {
    currentRoute: pathname,
    routeName,
    availableData,
    appInfo: {
      name: 'Datos 2025',
      version: '1.0.0',
      description: 'Aplicación React + TypeScript para visualización y gestión de datos'
    }
  }
}

/**
 * Hook to get the current application context
 * 
 * This hook uses react-router's useLocation to detect the current route
 * and builds a ChatContext object with relevant information.
 * 
 * @returns ChatContext object for the current route
 */
export function useAppContext(): ChatContext {
  const location = useLocation()
  return buildContextFromRoute(location.pathname)
}
