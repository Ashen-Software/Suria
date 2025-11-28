# Implementation Plan - Chatbot Integration

- [x] 1. Setup project dependencies and configuration





  - Install required npm packages: react-markdown, fast-check
  - Add environment variables to .env.example for OpenAI API configuration
  - Create TypeScript types file for chatbot domain models
  - _Requirements: 7.5, 10.1_

- [x] 2. Implement core data models and types





  - Define Message, ChatContext, LLMConfig, and ChatError interfaces
  - Create type guards for message validation
  - Define constants for routes and data availability mapping
  - _Requirements: 2.1, 3.1, 3.2, 7.1_

- [x] 2.1 Write property test for message validation


  - **Property 6: Empty message rejection**
  - **Validates: Requirements 2.5**

- [x] 3. Create LLM service layer





  - Implement LLMService class with OpenAI API integration
  - Create buildSystemPrompt method that includes app context
  - Implement sendMessage method with error handling
  - Add retry logic for transient failures
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 10.1_

- [x] 3.1 Write property test for LLM request structure


  - **Property 10: LLM request includes system prompt and history**
  - **Validates: Requirements 7.2, 7.3**

- [x] 3.2 Write unit tests for LLM service error handling


  - Test network error scenarios
  - Test API error responses
  - Test rate limiting handling
  - _Requirements: 7.4_

- [x] 4. Create application context service





  - Implement useAppContext hook to detect current route
  - Create buildContextFromRoute function to map routes to context
  - Add logic to determine available data based on current page
  - _Requirements: 3.1, 3.2, 3.4_

- [x] 4.1 Write property test for context route inclusion


  - **Property 7: Context includes current route**
  - **Validates: Requirements 3.1**

- [x] 4.2 Write property test for context data availability


  - **Property 8: Context includes available data**
  - **Validates: Requirements 3.2**

- [x] 5. Implement ChatbotContext provider





  - Create ChatbotContext with React Context API
  - Implement state management for messages, loading, and open/closed state
  - Create sendMessage action that calls LLM service
  - Create clearHistory action
  - Add state persistence logic for navigation
  - _Requirements: 1.3, 2.1, 2.2, 2.3, 2.4, 9.2_

- [x] 5.1 Write property test for state persistence


  - **Property 2: State persistence across navigation**
  - **Validates: Requirements 1.3**

- [x] 5.2 Write property test for message addition


  - **Property 3: Message addition to history**
  - **Validates: Requirements 2.1, 2.4**

- [x] 5.3 Write property test for history clearing


  - **Property 13: History clearing**
  - **Validates: Requirements 9.2**

- [x] 6. Create ChatbotButton component





  - Implement floating button with fixed positioning (bottom-right)
  - Add click handler to toggle chatbot open state
  - Style with TailwindCSS and DaisyUI (consistent with app design)
  - Add notification badge for unread messages (optional)
  - _Requirements: 1.1, 1.4, 8.1, 8.2_

- [x] 7. Create ChatMessage component





  - Implement message rendering with role-based styling
  - Add avatar/icon differentiation for user vs assistant
  - Integrate react-markdown for bot message rendering
  - Add timestamp display
  - Handle long message formatting with line breaks
  - _Requirements: 4.4, 8.3, 8.4, 8.5_

- [x] 7.1 Write property test for markdown rendering


  - **Property 11: Markdown rendering**
  - **Validates: Requirements 8.5**

- [x] 7.2 Write property test for long message formatting


  - **Property 12: Message formatting for long content**
  - **Validates: Requirements 8.4**

- [x] 8. Create ChatMessages component





  - Implement scrollable message list container
  - Add auto-scroll to bottom on new messages
  - Display loading indicator during message processing
  - Show empty state with suggested questions when no messages
  - _Requirements: 4.1, 4.2, 4.3, 2.3, 9.4_

- [x] 8.1 Write property test for history display


  - **Property 9: History display on open**
  - **Validates: Requirements 4.1**


- [x] 8.2 Write property test for loading state

  - **Property 5: Loading state during processing**
  - **Validates: Requirements 2.3**

- [x] 9. Create ChatInput component





  - Implement textarea with auto-resize
  - Add send button with click and Enter key handlers
  - Implement input validation (prevent empty messages)
  - Clear input field after successful send
  - Disable input during message processing
  - _Requirements: 2.1, 2.2, 2.5_

- [x] 9.1 Write property test for input clearing


  - **Property 4: Input field clearing**
  - **Validates: Requirements 2.2**

- [x] 10. Create ChatHeader component





  - Implement header with title "Asistente Virtual"
  - Add close button to collapse chatbot
  - Add clear history button with confirmation
  - Style consistently with app design
  - _Requirements: 1.2, 9.1, 9.3_

- [x] 11. Create ChatbotWindow component





  - Compose ChatHeader, ChatMessages, and ChatInput
  - Implement responsive sizing (min 350px, max 450px width)
  - Add slide-in/slide-out animation
  - Position fixed at bottom-right
  - Add shadow and border styling
  - _Requirements: 1.1, 1.2, 1.5, 8.1, 8.2_

- [x] 11.1 Write property test for widget toggle


  - **Property 1: Widget state toggle**
  - **Validates: Requirements 1.1, 1.2**

- [x] 12. Create ChatbotWidget main component





  - Integrate ChatbotButton and ChatbotWindow
  - Connect to ChatbotContext for state management
  - Implement conditional rendering based on open/closed state
  - Add keyboard shortcuts (Escape to close)
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 13. Integrate chatbot into App.tsx





  - Wrap app with ChatbotProvider
  - Mount ChatbotWidget at root level (outside main layout)
  - Verify chatbot appears on all pages
  - Test navigation state persistence
  - _Requirements: 1.3, 3.1, 3.2_

- [x] 14. Add markdown utilities and sanitization








  - Configure react-markdown with safe rendering options
  - Add syntax highlighting for code blocks (optional)
  - Implement link handling (open in new tab)
  - Sanitize output to prevent XSS
  - _Requirements: 8.5_

- [ ] 15. Implement error handling UI
  - Create error message component with retry button
  - Add error boundary for chatbot components
  - Display user-friendly error messages in Spanish
  - Add toast notifications for non-critical errors
  - _Requirements: 7.4_

- [ ] 16. Add accessibility features
  - Implement keyboard navigation (Tab, Enter, Escape)
  - Add ARIA labels and roles
  - Ensure focus management when opening/closing
  - Test with screen reader
  - Verify color contrast meets WCAG AA
  - _Requirements: 1.1, 1.2_

- [ ] 17. Optimize performance
  - Implement lazy loading for chatbot components
  - Add message history limit (keep last 20 messages in context)
  - Memoize expensive computations
  - Add debouncing for auto-resize textarea
  - _Requirements: 2.3, 4.1_

- [ ] 18. Create welcome message and suggested questions
  - Define initial welcome message in Spanish
  - Create list of suggested questions for empty state
  - Add click handlers to populate input with suggestions
  - _Requirements: 9.3, 9.4_

- [ ] 19. Final integration testing and polish
  - Test complete user flow: open → ask question → receive response → close
  - Verify all routes provide correct context
  - Test error scenarios (network failure, invalid API key)
  - Verify responsive behavior on different screen sizes
  - Check accessibility compliance
  - _Requirements: All_

- [ ] 20. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
