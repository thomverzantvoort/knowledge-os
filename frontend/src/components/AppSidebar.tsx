import type { ReactNode } from 'react'
import { History, Inbox, Library, LogOut } from 'lucide-react'
import { NavLink } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { useAuth } from '@/hooks/use-auth'
import { cn } from '@/lib/utils'

type NavItemProps = {
  to?: string
  icon: ReactNode
  label: string
  disabled?: boolean
  hint?: string
}

function NavItem({ to, icon, label, disabled, hint }: NavItemProps) {
  if (disabled || !to) {
    return (
      <div
        className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground opacity-60"
        aria-disabled="true"
      >
        {icon}
        <span className="flex flex-col">
          <span>{label}</span>
          {hint ? (
            <span className="text-xs text-muted-foreground">{hint}</span>
          ) : null}
        </span>
      </div>
    )
  }

  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        cn(
          'flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors',
          isActive
            ? 'bg-sidebar-accent text-sidebar-accent-foreground'
            : 'text-sidebar-foreground hover:bg-sidebar-accent/60',
        )
      }
    >
      {icon}
      <span>{label}</span>
    </NavLink>
  )
}

export function AppSidebar() {
  const { logout } = useAuth()

  return (
    <aside className="flex h-full w-56 shrink-0 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground">
      <div className="flex min-h-[5.5rem] shrink-0 items-center border-b border-sidebar-border px-6">
        <p className="font-heading text-base font-medium">Knowledge OS</p>
      </div>

      <nav className="flex flex-1 flex-col gap-1 p-3">
        <NavItem
          to="/history"
          icon={<History className="size-4" />}
          label="History"
        />
        <NavItem
          icon={<Inbox className="size-4" />}
          label="Inbox"
          disabled
          hint="Coming soon"
        />
        <NavItem
          icon={<Library className="size-4" />}
          label="Library"
          disabled
          hint="Coming soon"
        />
      </nav>

      <div className="shrink-0 border-t border-sidebar-border p-3">
        <Button
          variant="ghost"
          className="w-full justify-start gap-3 text-sidebar-foreground hover:bg-sidebar-accent/60"
          onClick={logout}
        >
          <LogOut className="size-4" />
          Sign out
        </Button>
      </div>
    </aside>
  )
}
