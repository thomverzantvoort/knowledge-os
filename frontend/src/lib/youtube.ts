export function formatTimestamp(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60

  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
  }

  return `${minutes}:${String(secs).padStart(2, '0')}`
}

export function youtubeUrlAt(url: string, seconds: number): string {
  const parsed = new URL(url)
  parsed.searchParams.set('t', String(seconds))
  return parsed.toString()
}
