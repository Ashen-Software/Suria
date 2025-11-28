# Design Document - Chatbot Integration

## Overview

Este documento describe el diseño técnico para integrar un chatbot conversacional en la aplicación React. El chatbot será un widget flotante que permite a los usuarios hacer preguntas sobre la aplicación, sus datos y funcionalidades. Utilizará un servicio de LLM (OpenAI GPT o similar) para generar respuestas contextuales basadas en el estado actual de la aplicación.

El chatbot se implementará como un componente React independiente que se montará globalmente en la aplicación, manteniendo su propio estado y contexto. La integración será no invasiva, permitiendo que el chatbot funcione sin modificar significativamente la estructura existente de la aplicación.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React Application                     │
│  ┌────────────────────────────────────────────────────┐ │
│  │              App Component                         │ │
│  │  ┌──────────────────┐  ┌──────────────────────┐  │ │
│  │  │   Main Layout    │  │  ChatbotWidget       │  │ │
│  │  │   (Routes)       │  │  (Global Overlay)    │  │ │
│  │  └──────────────────┘  └──────────────────────┘  │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              Chatbot Service Layer                       │
│  ┌──────────────────┐  ┌──────────────────────────┐   │
│  │  Context         │  │  LLM Service             │   │
│  │  Provider        │  │  (OpenAI/Anthropic)      │   │
│  └──────────────────┘  └──────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  External Services                       │
│              OpenAI API / Anthropic API                  │
└─────────────────────────────────────────────────────────┘
```

### Component Architecture

```
ChatbotWidget
├── ChatbotButton (collapsed state)
└── ChatbotWindow (expanded state)
    ├── ChatHeader
    │   ├── Title
    │   ├── ClearButton
    │   └── CloseButton
    ├── ChatMessages
    │   ├── MessageList
    │   │   ├── UserMessage
    │   │   └── BotMessage (with markdown support)
    │   └── LoadingIndicator
    └── ChatInput
        ├── TextArea
        └── SendButton
```

## Components and Interfaces

### 1. ChatbotWidget Component

Componente principal que maneja el estado del chatbot (abierto/cerrado) y orquesta los subcomponentes.

```typescript
interface ChatbotWidgetProps {
  position?: 'bottom-right' | 'bottom-left'
  defaultOpen?: boolean
}

interface ChatbotState {
  isOpen: boolean
  messages: Message[]
  isLoading: boolean
}
```

### 2. Message Types

```typescript
interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
}

interface ChatContext {
  currentRoute: string
  routeName: string
  availableData?: {
    territorios?: boolean
    tiempo?: boolean
    etlSources?: boolean
  }
}
```

### 3. LLM Service Interface

```typescript
interface LLMService {
  sendMessage(
    messages: Message[],
    context: ChatContext
  ): Promise<string>
  
  buildSystemPrompt(context: ChatContext): string
}

interface LLMConfig {
  apiKey: string
  model: string
  temperature?: number
  maxTokens?: number
}
```

### 4. Context Provider

```typescript
interface ChatbotContextValue {
  messages: Message[]
  isLoading: boolean
  sendMessage: (content: string) => Promise<void>
  clearHistory: () => void
  getContext: () => ChatContext
}
```

## Data Models

### Message Model

```typescript
type MessageRole = 'user' | 'assistant' | 'system'

interface Message {
  id: string              // UUID generado
  role: MessageRole       // Rol del mensaje
  content: string         // Contenido del mensaje
  timestamp: Date         // Momento de creación
}
```

### Chat Context Model

```typescript
interface ChatContext {
  // Información de navegación
  currentRoute: string    // Ej: '/territorios'
  routeName: string       // Ej: 'Territorios'
  
  // Información de datos disponibles
  availableData?: {
    territorios?: boolean
    tiempo?: boolean
    etlSources?: boolean
  }
  
  // Metadata de la aplicación
  appInfo: {
    name: string
    version: string
    description: string
  }
}
```

### LLM Configuration Model

```typescript
interface LLMConfig {
  provider: 'openai' | 'anthropic'  // Proveedor de LLM
  apiKey: string                     // API key desde env
  model: string                      // Modelo específico
  temperature: number                // 0-1, creatividad
  maxTokens: number                  // Límite de tokens
  systemPrompt: string               // Prompt base del sistema
}
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Widget state toggle

*For any* initial state of the chatbot widget (open or closed), clicking the toggle button should change the state to its opposite.
**Validates: Requirements 1.1, 1.2**

### Property 2: State persistence across navigation

*For any* chatbot state (open or closed) and any route change, the chatbot state should remain unchanged after navigation.
**Validates: Requirements 1.3**

### Property 3: Message addition to history

*For any* valid message (non-empty string) sent by either user or assistant, the message should appear in the conversation history with the correct role and timestamp.
**Validates: Requirements 2.1, 2.4**

### Property 4: Input field clearing

*For any* message sent through the chat input, the input field should be empty immediately after the message is sent.
**Validates: Requirements 2.2**

### Property 5: Loading state during processing

*For any* message being processed by the LLM service, the chatbot should display a loading indicator until the response is received or an error occurs.
**Validates: Requirements 2.3**

### Property 6: Empty message rejection

*For any* string composed entirely of whitespace characters (including empty strings), attempting to send it should be prevented and the message should not appear in the history.
**Validates: Requirements 2.5**

### Property 7: Context includes current route

*For any* message sent to the LLM service, the request context should include the current route path and route name.
**Validates: Requirements 3.1**

### Property 8: Context includes available data

*For any* message sent from a data page (territorios, tiempo, or etl), the request context should indicate which data is available on that page.
**Validates: Requirements 3.2**

### Property 9: History display on open

*For any* existing conversation history, opening the chatbot should display all messages from the current session in chronological order.
**Validates: Requirements 4.1**

### Property 10: LLM request includes system prompt and history

*For any* request sent to the LLM service, the request should include both the system prompt with application context and the recent conversation history.
**Validates: Requirements 7.2, 7.3**

### Property 11: Markdown rendering

*For any* assistant message containing valid markdown syntax, the rendered output should display the formatted HTML equivalent of that markdown.
**Validates: Requirements 8.5**

### Property 12: Message formatting for long content

*For any* message with content exceeding 100 characters, the message should be formatted with appropriate line breaks and spacing for readability.
**Validates: Requirements 8.4**

### Property 13: History clearing

*For any* conversation history of any length, invoking the clear history action should result in an empty message list.
**Validates: Requirements 9.2**

## Error Handling

### Error Scenarios

1. **LLM API Failures**
   - Network errors
   - API rate limiting
   - Invalid API key
   - Timeout errors

2. **Invalid Input**
   - Empty messages
   - Extremely long messages (> 4000 characters)
   - Invalid characters or encoding

3. **State Management Errors**
   - Failed to persist state
   - Corrupted message history

### Error Handling Strategy

```typescript
interface ChatError {
  type: 'network' | 'api' | 'validation' | 'unknown'
  message: string
  userMessage: string  // Mensaje amigable para el usuario
  retryable: boolean
}

class ChatbotErrorHandler {
  handleError(error: unknown): ChatError {
    // Clasificar y transformar errores
    // Retornar error estructurado con mensaje amigable
  }
  
  shouldRetry(error: ChatError): boolean {
    // Determinar si el error es recuperable
  }
}
```

### User-Facing Error Messages

- **Network Error**: "No se pudo conectar con el servicio. Por favor, verifica tu conexión a internet."
- **API Error**: "El servicio está temporalmente no disponible. Por favor, intenta de nuevo en unos momentos."
- **Rate Limit**: "Has alcanzado el límite de mensajes. Por favor, espera un momento antes de continuar."
- **Invalid Input**: "El mensaje no pudo ser procesado. Por favor, intenta con un mensaje diferente."

## Testing Strategy

### Unit Testing

La estrategia de testing se enfocará en verificar componentes individuales y su lógica de negocio:

**Components to Unit Test:**
1. **ChatbotWidget** - Estado de apertura/cierre, renderizado condicional
2. **ChatInput** - Validación de entrada, manejo de eventos
3. **MessageList** - Renderizado de mensajes, scroll automático
4. **LLMService** - Construcción de prompts, manejo de respuestas
5. **ContextProvider** - Detección de ruta, construcción de contexto

**Example Unit Tests:**
- Verificar que el botón de toggle cambia el estado del widget
- Verificar que mensajes vacíos son rechazados
- Verificar que el contexto incluye la ruta actual
- Verificar que los errores de API se manejan correctamente
- Verificar que el markdown se renderiza correctamente

### Property-Based Testing

Utilizaremos **fast-check** (biblioteca de property-based testing para TypeScript/JavaScript) para verificar las propiedades de corrección definidas anteriormente.

**Configuration:**
- Minimum 100 iterations per property test
- Use custom generators for domain-specific data (messages, routes, contexts)
- Tag each test with the property number and requirement reference

**Property Test Examples:**

```typescript
// Property 1: Widget state toggle
test('Property 1: Widget state toggle', () => {
  fc.assert(
    fc.property(fc.boolean(), (initialState) => {
      const widget = createWidget({ isOpen: initialState })
      widget.toggle()
      expect(widget.isOpen).toBe(!initialState)
    }),
    { numRuns: 100 }
  )
})

// Property 6: Empty message rejection
test('Property 6: Empty message rejection', () => {
  fc.assert(
    fc.property(fc.stringOf(fc.constantFrom(' ', '\t', '\n')), (emptyMsg) => {
      const result = validateMessage(emptyMsg)
      expect(result.isValid).toBe(false)
    }),
    { numRuns: 100 }
  )
})
```

**Custom Generators:**
- `arbitraryMessage()` - Genera mensajes válidos de usuario
- `arbitraryRoute()` - Genera rutas válidas de la aplicación
- `arbitraryContext()` - Genera contextos de aplicación válidos
- `arbitraryMessageHistory()` - Genera historiales de conversación

**Testing Requirements:**
- Each property-based test MUST be tagged with: `**Feature: chatbot-integration, Property {number}: {property_text}**`
- Each property-based test MUST run a minimum of 100 iterations
- Each correctness property MUST be implemented by a SINGLE property-based test
- Tests MUST use the fast-check library, not implement PBT from scratch

## Implementation Details

### Technology Stack

- **UI Framework**: React 19 with TypeScript
- **Styling**: TailwindCSS + DaisyUI (existing in project)
- **State Management**: React Context API + useState/useReducer
- **LLM Integration**: OpenAI API (GPT-4 or GPT-3.5-turbo)
- **Markdown Rendering**: react-markdown
- **HTTP Client**: fetch API (native)
- **Testing**: Vitest + fast-check

### File Structure

```
src/
├── components/
│   └── chatbot/
│       ├── ChatbotWidget.tsx          # Main widget component
│       ├── ChatbotButton.tsx          # Floating button
│       ├── ChatbotWindow.tsx          # Expanded chat window
│       ├── ChatHeader.tsx             # Header with title and actions
│       ├── ChatMessages.tsx           # Message list container
│       ├── ChatMessage.tsx            # Individual message component
│       ├── ChatInput.tsx              # Input field and send button
│       └── index.ts                   # Exports
├── contexts/
│   └── ChatbotContext.tsx             # Global chatbot state
├── services/
│   ├── llm.service.ts                 # LLM API integration
│   └── chatContext.service.ts         # Application context builder
├── hooks/
│   ├── useChatbot.ts                  # Hook to access chatbot context
│   └── useAppContext.ts               # Hook to get current app context
├── types/
│   └── chatbot.types.ts               # TypeScript interfaces
└── utils/
    └── markdown.utils.ts              # Markdown processing utilities
```

### Environment Variables

```bash
# .env
VITE_OPENAI_API_KEY=sk-...           # OpenAI API key
VITE_OPENAI_MODEL=gpt-4-turbo        # Model to use
VITE_CHATBOT_MAX_TOKENS=1000         # Max tokens per response
VITE_CHATBOT_TEMPERATURE=0.7         # Response creativity (0-1)
```

### System Prompt Template

```typescript
const SYSTEM_PROMPT = `
Eres un asistente virtual para una aplicación de gestión de datos llamada "Datos 2025".

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
- Página actual: {currentRoute}
- Datos disponibles: {availableData}

INSTRUCCIONES:
- Responde SIEMPRE en español
- Sé conciso y claro
- Proporciona ejemplos cuando sea útil
- Si no sabes algo, admítelo
- Ayuda con navegación, explicación de datos y funcionalidades
`
```

### Integration Points

1. **App.tsx Integration**
   ```typescript
   import { ChatbotProvider } from '@/contexts/ChatbotContext'
   import { ChatbotWidget } from '@/components/chatbot'
   
   function App() {
     return (
       <ChatbotProvider>
         <Layout>
           <AppRoutes />
         </Layout>
         <ChatbotWidget />
       </ChatbotProvider>
     )
   }
   ```

2. **Route Context Detection**
   ```typescript
   // Use react-router's useLocation hook
   const location = useLocation()
   const context = buildContextFromRoute(location.pathname)
   ```

3. **LLM Service Call Flow**
   ```
   User Input → Validation → Add to History → 
   Build Context → Call LLM API → Parse Response → 
   Add to History → Update UI
   ```

### Performance Considerations

1. **Debouncing**: No debouncing on send button (immediate feedback)
2. **Lazy Loading**: Load chatbot components only when first opened
3. **Message Limit**: Keep only last 20 messages in context to reduce token usage
4. **Caching**: Cache system prompt to avoid rebuilding on every message
5. **Optimistic Updates**: Show user message immediately, add bot response when ready

### Accessibility

1. **Keyboard Navigation**: Full keyboard support (Tab, Enter, Escape)
2. **ARIA Labels**: Proper labels for screen readers
3. **Focus Management**: Trap focus within chat window when open
4. **Color Contrast**: Ensure WCAG AA compliance
5. **Semantic HTML**: Use appropriate HTML elements

### Security Considerations

1. **API Key Protection**: Never expose API key in client code (use environment variables)
2. **Input Sanitization**: Sanitize user input before sending to LLM
3. **XSS Prevention**: Sanitize markdown output to prevent XSS attacks
4. **Rate Limiting**: Implement client-side rate limiting to prevent abuse
5. **Error Messages**: Don't expose sensitive information in error messages
