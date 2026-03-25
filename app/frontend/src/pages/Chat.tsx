import { AgentChat } from '@/components/vda/AgentChat'

export function Chat() {
  return (
    <div className="h-full -m-6">
      <AgentChat
        welcomeTitle="Welcome to AI Chat"
        welcomeSubtitle="Ask me anything about your data"
        suggestedPrompts={[
          'Show me a summary of recent activity',
          'What anomalies were detected today?',
          'Create a work order for maintenance',
        ]}
      />
    </div>
  )
}
