import React from 'react'
import ReactDOM from 'react-dom/client'
import './styles/globals.css'

document.documentElement.setAttribute('data-theme', 'neutral-dark')

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <div className="bg-surface-primary text-content-primary p-8">
      <h1 className="text-2xl font-bold text-accent">VDA Theme System Working</h1>
    </div>
  </React.StrictMode>,
)
