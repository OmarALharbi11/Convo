import { format, formatDistanceToNow, parseISO } from 'date-fns'

export const formatDate = (iso: string): string => {
  try {
    return format(parseISO(iso), 'EEE, dd MMM yyyy')
  } catch {
    return iso
  }
}

export const formatTime = (iso: string): string => {
  try {
    return format(parseISO(iso), 'h:mm a')
  } catch {
    return iso
  }
}

export const formatDateTime = (iso: string): string => {
  try {
    return format(parseISO(iso), 'dd MMM yyyy, h:mm a')
  } catch {
    return iso
  }
}

export const formatRelativeTime = (iso: string): string => {
  try {
    return formatDistanceToNow(parseISO(iso), { addSuffix: true })
  } catch {
    return iso
  }
}

export const formatDuration = (startIso: string, endIso: string): string => {
  try {
    const start = parseISO(startIso)
    const end = parseISO(endIso)
    const minutes = Math.round((end.getTime() - start.getTime()) / 60000)
    if (minutes < 60) return `${minutes}m`
    const hours = Math.floor(minutes / 60)
    const rem = minutes % 60
    return rem > 0 ? `${hours}h ${rem}m` : `${hours}h`
  } catch {
    return ''
  }
}

export const truncate = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength - 3) + '...'
}

export const intentToLabel = (intent: string): string => {
  const labels: Record<string, string> = {
    read_emails: 'Read Emails',
    summarise_emails: 'Summarise Emails',
    send_email: 'Send Email',
    list_calendar_events: 'Calendar',
    check_availability: 'Availability',
    create_meeting: 'Schedule Meeting',
    modify_meeting: 'Modify Meeting',
    delete_meeting: 'Cancel Meeting',
    show_employee_calendar: 'Team Calendar',
    read_notifications: 'Notifications',
    help: 'Help',
    repeat_last_response: 'Repeat',
    unknown: 'Unknown',
  }
  return labels[intent] ?? intent.replace(/_/g, ' ')
}

export const getUrgencyColor = (level: string): string => {
  if (level === 'high') return 'text-red-600 bg-red-50'
  if (level === 'medium') return 'text-yellow-600 bg-yellow-50'
  return 'text-green-600 bg-green-50'
}

export const getSentimentIcon = (sentiment: string): string => {
  if (sentiment === 'positive') return '😊'
  if (sentiment === 'negative') return '⚠️'
  return '😐'
}

export const getImportanceColor = (importance: string): string => {
  if (importance === 'high') return 'text-red-500'
  if (importance === 'low') return 'text-slate-400'
  return 'text-slate-600'
}

export const getAuditOutcomeColor = (outcome: string): string => {
  if (outcome === 'success') return 'bg-green-100 text-green-700'
  if (outcome === 'denied') return 'bg-orange-100 text-orange-700'
  return 'bg-red-100 text-red-700'
}

export const getIntentColor = (intent: string): string => {
  if (intent.includes('email')) return 'bg-blue-100 text-blue-700'
  if (intent.includes('calendar') || intent.includes('meeting') || intent.includes('availability')) return 'bg-green-100 text-green-700'
  if (intent === 'unknown') return 'bg-gray-100 text-gray-600'
  if (intent === 'help') return 'bg-purple-100 text-purple-700'
  return 'bg-slate-100 text-slate-700'
}
