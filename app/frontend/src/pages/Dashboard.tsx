import { LayoutDashboard, Users, AlertTriangle, TrendingUp } from 'lucide-react'
import { KPIDashboard } from '@/components/vda/KPIDashboard'
import { MetricsBar } from '@/components/vda/MetricsBar'
import type { KPIMetric } from '@/types'

const sampleMetrics: KPIMetric[] = [
  { label: 'Total Assets', value: 1284, change: 5.2, trend: 'up', icon: LayoutDashboard },
  { label: 'Active Users', value: 342, change: -2.1, trend: 'down', icon: Users },
  { label: 'Open Alerts', value: 17, change: 12.5, trend: 'up', icon: AlertTriangle },
  { label: 'Efficiency', value: '94.7%', change: 1.3, trend: 'up', icon: TrendingUp },
]

export function Dashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-content-primary">Dashboard</h1>
        <p className="text-content-secondary mt-1">Overview of your operations</p>
      </div>
      <KPIDashboard metrics={sampleMetrics} columns={4} />
      <MetricsBar
        metrics={[
          { label: 'Uptime', value: '99.7%' },
          { label: 'Throughput', value: '1.2K/hr' },
          { label: 'Latency', value: '45ms' },
        ]}
        variant="full"
      />
      <div className="bg-surface-card border border-border rounded-lg p-6">
        <h2 className="text-lg font-semibold text-content-primary mb-4">Sample Data Table</h2>
        <p className="text-content-muted text-sm">
          DataExplorer will show data from API endpoints when connected to a backend.
        </p>
      </div>
    </div>
  )
}
