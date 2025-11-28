/**
 * ChatHeader Component
 * 
 * Header for the chatbot window with title, close button, and clear history button.
 * Styled consistently with TailwindCSS and DaisyUI.
 */

import { useState } from 'react'
import { useChatbot } from '@/contexts/ChatbotContext'

/**
 * ChatHeader Component
 * 
 * Displays the chatbot title "Asistente Virtual" with action buttons:
 * - Close button to collapse the chatbot
 * - Clear history button with confirmation dialog
 */
export function ChatHeader() {
  const { toggleOpen, clearHistory } = useChatbot()
  const [showConfirmation, setShowConfirmation] = useState(false)
  
  /**
   * Handle clear history button click
   * Shows confirmation dialog
   */
  const handleClearClick = () => {
    setShowConfirmation(true)
  }
  
  /**
   * Handle confirmation of clear history
   */
  const handleConfirmClear = () => {
    clearHistory()
    setShowConfirmation(false)
  }
  
  /**
   * Handle cancellation of clear history
   */
  const handleCancelClear = () => {
    setShowConfirmation(false)
  }
  
  return (
    <>
      <div className="flex items-center justify-between border-b border-base-300 bg-primary p-4 text-primary-content">
        {/* Title */}
        <h2 className="text-lg font-semibold" data-testid="chat-header-title">
          Asistente Virtual
        </h2>
        
        {/* Action buttons */}
        <div className="flex items-center gap-2">
          {/* Clear history button */}
          <button
            onClick={handleClearClick}
            className="btn btn-ghost btn-sm btn-circle"
            aria-label="Limpiar historial"
            title="Limpiar historial"
            data-testid="clear-history-button"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
              className="h-5 w-5"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"
              />
            </svg>
          </button>
          
          {/* Close button */}
          <button
            onClick={toggleOpen}
            className="btn btn-ghost btn-sm btn-circle"
            aria-label="Cerrar asistente"
            title="Cerrar"
            data-testid="close-button"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
              className="h-5 w-5"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      </div>
      
      {/* Confirmation dialog */}
      {showConfirmation && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50" data-testid="confirmation-dialog">
          <div className="card w-96 bg-base-100 shadow-xl">
            <div className="card-body">
              <h3 className="card-title">¿Limpiar historial?</h3>
              <p className="text-sm text-base-content/70">
                Esta acción eliminará todos los mensajes de la conversación actual. Esta acción no se puede deshacer.
              </p>
              <div className="card-actions justify-end mt-4">
                <button
                  onClick={handleCancelClear}
                  className="btn btn-ghost btn-sm"
                  data-testid="cancel-clear-button"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleConfirmClear}
                  className="btn btn-error btn-sm"
                  data-testid="confirm-clear-button"
                >
                  Limpiar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
