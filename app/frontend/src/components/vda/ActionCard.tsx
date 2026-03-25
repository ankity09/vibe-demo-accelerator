import { motion } from 'framer-motion'
import type { ActionCardData } from '@/types'
import { cn } from '@/lib/utils'

interface ActionCardProps {
  card: ActionCardData
  onAction: (action: string, id: string) => void
}

export function ActionCard({ card, onAction }: ActionCardProps) {
  return (
    <motion.div
      className="bg-surface-card border border-border rounded-lg p-4"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {/* Header: Type and Title */}
      <div className="mb-3">
        <span className="text-xs uppercase tracking-wider text-content-muted font-medium">
          {card.type}
        </span>
        <h3 className="text-content-primary font-semibold mt-1">
          {card.title}
        </h3>
      </div>

      {/* Details Grid */}
      {Object.keys(card.details).length > 0 && (
        <div className="mb-4 space-y-2">
          {Object.entries(card.details).map(([key, value]) => (
            <div key={key} className="flex items-center gap-2">
              <span className="text-content-muted text-sm font-medium min-w-[120px]">
                {key}:
              </span>
              <span className="text-content-primary text-sm">
                {value}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2 flex-wrap pt-3 border-t border-border">
        {card.actions.map((action) => (
          <button
            key={action}
            onClick={() => onAction(action, card.id)}
            className={cn(
              'text-xs px-3 py-1.5 rounded-md font-medium capitalize transition-colors',
              action === 'approve' && 'bg-success/10 text-success hover:bg-success/20',
              action === 'dismiss' && 'bg-surface-hover text-content-muted hover:bg-surface-secondary',
              action !== 'approve' && action !== 'dismiss' && 'bg-accent/10 text-accent hover:bg-accent/20'
            )}
          >
            {action}
          </button>
        ))}
      </div>
    </motion.div>
  )
}
