import { WorkflowPanel } from '@/components/vda/WorkflowPanel'

export function Workflows() {
  return (
    <WorkflowPanel
      agentSteps={{
        'anomaly_detection': ['Data Query', 'Analysis', 'Risk Assessment', 'Work Order'],
        'maintenance': ['Lookup', 'Scheduling', 'Notification', 'Confirmation'],
      }}
    />
  )
}
