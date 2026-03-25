import { motion } from 'framer-motion'
import { ArrowUp, ArrowDown } from 'lucide-react'
import type { KPIMetric } from '@/types'
import { cn, formatNumber, formatPercent } from '@/lib/utils'

interface KPIDashboardProps {
  metrics: KPIMetric[]
  columns?: 3 | 4 | 5
  loading?: boolean
}

const colsClass: Record<number, string> = {
  3: 'md:grid-cols-3',
  4: 'md:grid-cols-4',
  5: 'md:grid-cols-5',
}

export function KPIDashboard({ metrics, columns = 4, loading = false }: KPIDashboardProps) {
  if (loading) {
    return (
      <div className={cn('grid grid-cols-2 gap-4', colsClass[columns])}>
        {Array.from({ length: columns }).map((_, i) => (
          <div
            key={i}
            className="animate-pulse bg-surface-hover h-24 rounded-lg"
          />
        ))}
      </div>
    )
  }

  return (
    <div className={cn('grid grid-cols-2 gap-4', colsClass[columns])}>
      {metrics.map((metric, index) => {
        const Icon = metric.icon
        const isUp = metric.trend === 'up'
        const isDown = metric.trend === 'down'
        const valueStr =
          typeof metric.value === 'number' ? formatNumber(metric.value) : metric.value

        return (
          <motion.div
            key={metric.label}
            className="bg-surface-card border border-border rounded-lg p-4"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05, duration: 0.3 }}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <p className="text-content-muted text-sm truncate">{metric.label}</p>
                <p
                  className="text-2xl font-bold text-content-primary mt-1 truncate"
                  style={metric.color ? { color: metric.color } : undefined}
                >
                  {valueStr}
                </p>
                {metric.change !== undefined && metric.trend !== 'flat' && (
                  <div
                    className={cn(
                      'flex items-center gap-1 mt-1 text-xs font-medium',
                      isUp && 'text-green-500',
                      isDown && 'text-red-500',
                      !isUp && !isDown && 'text-content-muted'
                    )}
                  >
                    {isUp && <ArrowUp size={12} />}
                    {isDown && <ArrowDown size={12} />}
                    <span>{formatPercent(metric.change)}</span>
                  </div>
                )}
              </div>
              {Icon && (
                <div className="ml-3 flex-shrink-0">
                  <Icon
                    size={20}
                    className="text-content-muted"
                    style={metric.color ? { color: metric.color } : undefined}
                  />
                </div>
              )}
            </div>
          </motion.div>
        )
      })}
    </div>
  )
}
