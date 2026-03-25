import { useCallback, useEffect, useState } from 'react'

export type Theme = 'industrial' | 'medical' | 'corporate' | 'neutral'
export type Mode = 'light' | 'dark'

const STORAGE_KEY_THEME = 'vda-theme'
const STORAGE_KEY_MODE = 'vda-mode'

export function useTheme(defaultTheme: Theme = 'neutral', defaultMode: Mode = 'dark') {
  const [theme, setThemeState] = useState<Theme>(() => {
    return (localStorage.getItem(STORAGE_KEY_THEME) as Theme) || defaultTheme
  })
  const [mode, setModeState] = useState<Mode>(() => {
    return (localStorage.getItem(STORAGE_KEY_MODE) as Mode) || defaultMode
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', `${theme}-${mode}`)
    localStorage.setItem(STORAGE_KEY_THEME, theme)
    localStorage.setItem(STORAGE_KEY_MODE, mode)
  }, [theme, mode])

  const setTheme = useCallback((t: Theme) => setThemeState(t), [])
  const toggleMode = useCallback(() => {
    setModeState((m) => (m === 'dark' ? 'light' : 'dark'))
  }, [])

  return { theme, mode, setTheme, toggleMode }
}
