import { useState, useRef, useEffect } from 'react'
import { Sun, Moon } from 'lucide-react'
import { useTheme } from '@/hooks/useTheme'
import type { Theme } from '@/hooks/useTheme'
import { cn } from '@/lib/utils'

interface ThemeToggleProps {
  position?: 'nav' | 'floating'
}

interface ThemeOption {
  value: Theme
  label: string
  dot: string
}

const THEME_OPTIONS: ThemeOption[] = [
  { value: 'industrial', label: 'Industrial', dot: '#F59E0B' },
  { value: 'medical', label: 'Medical', dot: '#14B8A6' },
  { value: 'corporate', label: 'Corporate', dot: '#3B82F6' },
  { value: 'neutral', label: 'Neutral', dot: '#10B981' },
]

export function ThemeToggle({ position = 'nav' }: ThemeToggleProps) {
  const { theme, mode, setTheme, toggleMode } = useTheme()
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleThemeSelect = (t: Theme) => {
    setTheme(t)
    setOpen(false)
  }

  if (position === 'floating') {
    return (
      <div ref={containerRef} className="fixed bottom-4 right-4 z-50">
        <button
          onClick={toggleMode}
          className="w-10 h-10 rounded-full bg-surface-card border border-border flex items-center justify-center text-content-muted hover:text-content-primary hover:bg-surface-hover transition-colors shadow-lg"
          aria-label="Toggle dark/light mode"
        >
          {mode === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
        </button>
      </div>
    )
  }

  return (
    <div ref={containerRef} className="relative">
      <div className="flex items-center gap-1">
        <button
          onClick={toggleMode}
          className="p-1.5 rounded text-content-muted hover:text-content-primary hover:bg-surface-hover transition-colors"
          aria-label="Toggle dark/light mode"
        >
          {mode === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
        </button>
        <button
          onClick={() => setOpen((prev) => !prev)}
          className="flex items-center gap-1.5 px-2 py-1.5 rounded text-content-muted hover:text-content-primary hover:bg-surface-hover transition-colors text-xs"
          aria-label="Select theme"
          aria-expanded={open}
        >
          <span
            className="w-2.5 h-2.5 rounded-full flex-shrink-0"
            style={{
              backgroundColor:
                THEME_OPTIONS.find((o) => o.value === theme)?.dot ?? '#10B981',
            }}
          />
          <span className="capitalize">{theme}</span>
        </button>
      </div>

      {open && (
        <div className="absolute right-0 top-full mt-1 w-40 bg-surface-card border border-border rounded-lg shadow-lg overflow-hidden z-50">
          {THEME_OPTIONS.map((option) => (
            <button
              key={option.value}
              onClick={() => handleThemeSelect(option.value)}
              className={cn(
                'w-full flex items-center gap-2.5 px-3 py-2 text-sm text-left transition-colors',
                theme === option.value
                  ? 'bg-surface-hover text-content-primary'
                  : 'text-content-muted hover:bg-surface-hover hover:text-content-primary'
              )}
            >
              <span
                className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                style={{ backgroundColor: option.dot }}
              />
              {option.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
