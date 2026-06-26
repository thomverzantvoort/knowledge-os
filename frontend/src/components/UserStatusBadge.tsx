import type { UserStatus } from '@/lib/types'
import { USER_STATUS_LABELS } from '@/lib/types'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

const STATUS_VARIANTS: Record<
  UserStatus,
  'default' | 'secondary' | 'outline'
> = {
  unread: 'default',
  interested: 'secondary',
  dismissed: 'outline',
}

type UserStatusBadgeProps = {
  status: UserStatus
  className?: string
}

export function UserStatusBadge({ status, className }: UserStatusBadgeProps) {
  return (
    <Badge variant={STATUS_VARIANTS[status]} className={cn(className)}>
      {USER_STATUS_LABELS[status]}
    </Badge>
  )
}
