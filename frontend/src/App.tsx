import { AppRoutes } from '@/routes'
import { Layout } from '@/components/layout'
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

export default App
