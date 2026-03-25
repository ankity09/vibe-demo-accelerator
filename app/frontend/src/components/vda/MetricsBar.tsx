import type { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

interface MetricItem {
  label: string
  value: string | number
  icon?: LucideIcon
}

interface MetricsBarProps {
  metrics: MetricItem[]
  variant?: 'compact' | 'full'
}

export function MetricsBar({ metrics, variant = 'compact' }: MetricsBarProps) {
  const gapClass = variant === 'compact' ? 'gap-6' : 'gap-8'
  const valueSizeClass = variant === 'compact' ? 'text-sm' : 'text-lg'

  return (
    <div className={cn('flex items-center flex-wrap', gapClass)}>
      {metrics.map((item, index) => {
        const Icon = item.icon
        const isLast = index === metrics.length - 1

        return (
          <div
            key={item.label}
            className={cn(
              'flex items-center gap-2',
              !isLast && 'border-r border-border',
              !isLast && (variant === 'compact' ? 'pr-6' : 'pr-8')
            )}
          >
            {Icon && <Icon size={16} className="text-content-muted flex-shrink-0" />}
            <div>
              <p className="text-content-muted text-xs leading-none mb-0.5">{item.label}</p>
              <p className={cn('text-content-primary font-semibold leading-none', valueSizeClass)}>
                {item.value}
              </p>
            </div>
          </div>
        )
      })}
    </div>
  )
}
