import type { RouteConfig } from '@/types'
import { SidebarLayout } from './SidebarLayout'
import { TopNavLayout } from './TopNavLayout'
import { DashboardLayout } from './DashboardLayout'

interface AppShellProps {
  layout: 'sidebar' | 'topnav' | 'dashboard'
  demoName: string
  routes: RouteConfig[]
  logo?: React.ReactNode
  headerRight?: React.ReactNode
  children: React.ReactNode
}

export function AppShell({ layout, children, ...props }: AppShellProps) {
  switch (layout) {
    case 'topnav':
      return <TopNavLayout {...props}>{children}</TopNavLayout>
    case 'dashboard':
      return <DashboardLayout {...props}>{children}</DashboardLayout>
    default:
      return <SidebarLayout {...props}>{children}</SidebarLayout>
  }
}
