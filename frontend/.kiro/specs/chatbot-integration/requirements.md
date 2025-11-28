# Requirements Document

## Introduction

Este documento define los requisitos para integrar un chatbot conversacional en la aplicación React que permita a los usuarios hacer preguntas sobre la aplicación, sus funcionalidades, datos y navegación. El chatbot debe proporcionar respuestas contextuales basadas en el estado actual de la aplicación y ayudar a los usuarios a entender y utilizar mejor el sistema.

## Glossary

- **Chatbot**: Componente de interfaz conversacional que permite interacción mediante texto
- **Sistema**: La aplicación React + TypeScript + Vite con Supabase
- **Usuario**: Persona que interactúa con la aplicación y el chatbot
- **Contexto de Aplicación**: Información sobre la página actual, datos visibles y estado de la aplicación
- **LLM**: Large Language Model, modelo de lenguaje utilizado para generar respuestas
- **Widget de Chat**: Componente UI flotante que contiene la interfaz del chatbot
- **Historial de Conversación**: Registro de mensajes intercambiados entre usuario y chatbot
- **Prompt del Sistema**: Instrucciones iniciales que definen el comportamiento del chatbot

## Requirements

### Requirement 1

**User Story:** Como usuario, quiero abrir y cerrar el chatbot fácilmente, para que pueda acceder a ayuda cuando la necesite sin que interfiera con mi trabajo.

#### Acceptance Criteria

1. WHEN el usuario hace clic en el botón flotante del chatbot, THEN el Sistema SHALL mostrar la ventana del chat expandida
2. WHEN la ventana del chat está abierta y el usuario hace clic en el botón de cerrar, THEN el Sistema SHALL colapsar la ventana y mostrar solo el botón flotante
3. WHEN el usuario navega entre páginas, THEN el Sistema SHALL mantener el estado del chatbot (abierto o cerrado)
4. THE Sistema SHALL posicionar el widget del chatbot en la esquina inferior derecha de la pantalla
5. WHEN el widget está abierto, THEN el Sistema SHALL tener un ancho mínimo de 350px y un ancho máximo de 450px

### Requirement 2

**User Story:** Como usuario, quiero enviar mensajes al chatbot y recibir respuestas, para que pueda obtener información sobre la aplicación.

#### Acceptance Criteria

1. WHEN el usuario escribe un mensaje y presiona Enter o hace clic en enviar, THEN el Sistema SHALL agregar el mensaje al historial de conversación
2. WHEN un mensaje es enviado, THEN el Sistema SHALL limpiar el campo de entrada
3. WHEN el Sistema está procesando una respuesta, THEN el Sistema SHALL mostrar un indicador de carga
4. WHEN el chatbot genera una respuesta, THEN el Sistema SHALL agregar la respuesta al historial de conversación
5. WHEN el usuario intenta enviar un mensaje vacío, THEN el Sistema SHALL prevenir el envío

### Requirement 3

**User Story:** Como usuario, quiero que el chatbot entienda el contexto de la página actual, para que pueda darme respuestas relevantes sobre lo que estoy viendo.

#### Acceptance Criteria

1. WHEN el usuario hace una pregunta, THEN el Sistema SHALL incluir información sobre la ruta actual en el contexto
2. WHEN el usuario está en una página con datos, THEN el Sistema SHALL incluir información sobre los datos visibles en el contexto
3. WHEN el usuario pregunta sobre funcionalidades, THEN el Sistema SHALL proporcionar respuestas basadas en las capacidades reales de la aplicación
4. THE Sistema SHALL mantener un prompt del sistema que describe la arquitectura y funcionalidades de la aplicación

### Requirement 4

**User Story:** Como usuario, quiero ver el historial de mi conversación con el chatbot, para que pueda revisar respuestas anteriores.

#### Acceptance Criteria

1. WHEN el usuario abre el chatbot, THEN el Sistema SHALL mostrar todos los mensajes previos de la sesión actual
2. WHEN se agregan nuevos mensajes, THEN el Sistema SHALL hacer scroll automáticamente al mensaje más reciente
3. WHEN el historial es largo, THEN el Sistema SHALL permitir scroll para ver mensajes anteriores
4. THE Sistema SHALL distinguir visualmente entre mensajes del usuario y mensajes del chatbot
5. WHEN el usuario cierra y reabre el chatbot, THEN el Sistema SHALL preservar el historial de la sesión actual

### Requirement 5

**User Story:** Como usuario, quiero que el chatbot responda preguntas sobre la estructura de datos y tablas, para que pueda entender mejor la información mostrada.

#### Acceptance Criteria

1. WHEN el usuario pregunta sobre dim_territorios, THEN el Sistema SHALL proporcionar información sobre la estructura y campos de la tabla
2. WHEN el usuario pregunta sobre dim_tiempo, THEN el Sistema SHALL proporcionar información sobre la estructura y campos de la tabla
3. WHEN el usuario pregunta sobre etl_sources, THEN el Sistema SHALL proporcionar información sobre la estructura y campos de la tabla
4. WHEN el usuario pregunta sobre relaciones entre tablas, THEN el Sistema SHALL explicar las conexiones y dependencias

### Requirement 6

**User Story:** Como usuario, quiero que el chatbot me ayude con la navegación, para que pueda encontrar rápidamente las páginas que necesito.

#### Acceptance Criteria

1. WHEN el usuario pregunta cómo navegar a una página específica, THEN el Sistema SHALL proporcionar instrucciones claras
2. WHEN el usuario pregunta qué páginas están disponibles, THEN el Sistema SHALL listar todas las rutas principales de la aplicación
3. WHEN el usuario pregunta sobre funcionalidades de una página, THEN el Sistema SHALL describir las capacidades disponibles en esa página

### Requirement 7

**User Story:** Como desarrollador, quiero integrar un servicio de LLM para generar respuestas, para que el chatbot pueda proporcionar respuestas inteligentes y contextuales.

#### Acceptance Criteria

1. THE Sistema SHALL utilizar una API de LLM para generar respuestas del chatbot
2. WHEN se envía una solicitud al LLM, THEN el Sistema SHALL incluir el prompt del sistema con contexto de la aplicación
3. WHEN se envía una solicitud al LLM, THEN el Sistema SHALL incluir el historial de conversación reciente
4. WHEN la API del LLM falla, THEN el Sistema SHALL mostrar un mensaje de error amigable al usuario
5. THE Sistema SHALL configurar la API key del LLM mediante variables de entorno

### Requirement 8

**User Story:** Como usuario, quiero que el chatbot tenga una interfaz atractiva y fácil de usar, para que la experiencia sea agradable.

#### Acceptance Criteria

1. THE Sistema SHALL utilizar los estilos de TailwindCSS y DaisyUI consistentes con el resto de la aplicación
2. WHEN se muestra el chatbot, THEN el Sistema SHALL usar colores y tipografía coherentes con el diseño existente
3. THE Sistema SHALL mostrar avatares o iconos para diferenciar mensajes del usuario y del chatbot
4. WHEN hay mensajes largos, THEN el Sistema SHALL formatearlos de manera legible con saltos de línea apropiados
5. THE Sistema SHALL soportar formato markdown en las respuestas del chatbot

### Requirement 9

**User Story:** Como usuario, quiero poder limpiar el historial de conversación, para que pueda empezar una nueva conversación desde cero.

#### Acceptance Criteria

1. THE Sistema SHALL proporcionar un botón para limpiar el historial de conversación
2. WHEN el usuario hace clic en limpiar historial, THEN el Sistema SHALL eliminar todos los mensajes de la conversación actual
3. WHEN el historial es limpiado, THEN el Sistema SHALL mostrar un mensaje de bienvenida inicial
4. WHEN el historial está vacío, THEN el Sistema SHALL mostrar un estado vacío con sugerencias de preguntas

### Requirement 10

**User Story:** Como usuario, quiero que el chatbot responda en español, para que pueda comunicarme en mi idioma nativo.

#### Acceptance Criteria

1. THE Sistema SHALL configurar el LLM para responder en español
2. WHEN el usuario escribe en español, THEN el Sistema SHALL responder en español
3. WHEN el usuario escribe en inglés, THEN el Sistema SHALL responder en español a menos que se solicite explícitamente otro idioma
4. THE Sistema SHALL usar terminología técnica apropiada en español
