/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_SUPABASE_URL: string
  readonly VITE_SUPABASE_ANON_KEY: string
  readonly VITE_OPENAI_API_KEY?: string
  readonly VITE_OPENAI_MODEL?: string
  readonly VITE_CHATBOT_TEMPERATURE?: string
  readonly VITE_CHATBOT_MAX_TOKENS?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
