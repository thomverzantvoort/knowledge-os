import { Outlet } from 'react-router-dom'

import { AppSidebar } from '@/components/AppSidebar'

export function AppLayout() {
  return (
    <div className="flex h-svh overflow-hidden bg-background">
      <AppSidebar />
      <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
        <Outlet />
      </div>
    </div>
  )
}
