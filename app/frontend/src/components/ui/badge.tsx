import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-accent/50 focus:ring-offset-2',
  {
    variants: {
      variant: {
        default:
          'border-transparent bg-accent text-white',
        secondary:
          'border-transparent bg-surface-card text-content-secondary border border-border',
        destructive:
          'border-transparent bg-error/20 text-error border border-error/30',
        outline:
          'text-content-primary border border-border',
        success:
          'border-transparent bg-success/20 text-success border border-success/30',
        warning:
          'border-transparent bg-warning/20 text-warning border border-warning/30',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge, badgeVariants }
