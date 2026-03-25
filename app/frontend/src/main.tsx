import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { App } from './App'
import { demoConfig } from './demo-config'
import './styles/globals.css'

document.documentElement.setAttribute('data-theme', `${demoConfig.theme}-${demoConfig.mode}`)

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
