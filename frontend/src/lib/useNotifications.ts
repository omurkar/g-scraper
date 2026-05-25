'use client'

import { useCallback, useRef } from 'react'

type NotifPayload = {
  title: string
  body: string
  tag?: string
  /** If provided, clicking the notification opens this URL */
  actionUrl?: string
}

/** Play a soft chime using Web Audio API (no external file needed) */
function playChime(type: 'start' | 'done' | 'progress' = 'done') {
  try {
    const ctx = new (window.AudioContext || (window as any).webkitAudioContext)()
    const freqs = type === 'start' ? [523, 659] : type === 'progress' ? [440] : [659, 784, 1047]
    let t = ctx.currentTime
    freqs.forEach((freq, i) => {
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.frequency.value = freq
      osc.type = 'sine'
      gain.gain.setValueAtTime(0, t)
      gain.gain.linearRampToValueAtTime(0.18, t + 0.05)
      gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.35)
      osc.start(t)
      osc.stop(t + 0.35)
      t += 0.18
    })
    // Auto-close after notes play
    setTimeout(() => ctx.close(), 1500)
  } catch {
    // AudioContext not available (SSR / headless) — silently ignore
  }
}

export function useNotifications() {
  const permissionRef = useRef<NotificationPermission>('default')

  /** Request permission once — safe to call multiple times */
  const requestPermission = useCallback(async (): Promise<boolean> => {
    if (typeof window === 'undefined' || !('Notification' in window)) return false
    if (Notification.permission === 'granted') {
      permissionRef.current = 'granted'
      return true
    }
    if (Notification.permission === 'denied') return false
    const result = await Notification.requestPermission()
    permissionRef.current = result
    return result === 'granted'
  }, [])

  /** Send a desktop notification + optional chime */
  const notify = useCallback(
    (payload: NotifPayload, chime?: 'start' | 'done' | 'progress') => {
      // Always play chime regardless of notification permission
      if (chime) playChime(chime)

      if (typeof window === 'undefined' || !('Notification' in window)) return
      if (Notification.permission !== 'granted') return

      const n = new Notification(payload.title, {
        body: payload.body,
        icon: '/favicon.ico',
        badge: '/favicon.ico',
        tag: payload.tag ?? 'leadscout',
        requireInteraction: chime === 'done', // keep "job done" notification visible
      })

      if (payload.actionUrl) {
        n.onclick = () => {
          window.focus()
          n.close()
        }
      }
    },
    []
  )

  return { requestPermission, notify }
}
