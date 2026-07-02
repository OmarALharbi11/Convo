/**
 * Typed fetch-based API client.
 *
 * Reads the JWT from localStorage (set by the auth store).
 * Handles 401 → redirect to login.
 * All responses are parsed as JSON.
 */

const getToken = (): string | null => {
  try {
    const raw = localStorage.getItem('ipa-auth')
    if (!raw) return null
    const parsed = JSON.parse(raw)
    return parsed?.state?.token ?? null
  } catch {
    return null
  }
}

const buildHeaders = (extra?: Record<string, string>): Record<string, string> => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...extra,
  }
  const token = getToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

const handleResponse = async <T>(response: Response): Promise<T> => {
  if (response.status === 401) {
    localStorage.removeItem('ipa-auth')
    window.location.href = '/login'
    throw new Error('Session expired. Please sign in again.')
  }

  if (!response.ok) {
    let message = `HTTP ${response.status}`
    try {
      const body = await response.json()
      message = body.detail || body.message || JSON.stringify(body)
    } catch {
      message = response.statusText || message
    }
    throw new Error(message)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

const buildUrl = (path: string, params?: Record<string, string | number | boolean | undefined>): string => {
  const url = new URL(path, window.location.origin)
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) {
        url.searchParams.set(k, String(v))
      }
    })
  }
  return url.toString()
}

export const apiClient = {
  get: async <T>(path: string, params?: Record<string, string | number | boolean | undefined>): Promise<T> => {
    const response = await fetch(buildUrl(path, params), {
      method: 'GET',
      headers: buildHeaders(),
    })
    return handleResponse<T>(response)
  },

  post: async <T>(path: string, body?: unknown): Promise<T> => {
    const response = await fetch(buildUrl(path), {
      method: 'POST',
      headers: buildHeaders(),
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
    return handleResponse<T>(response)
  },

  patch: async <T>(path: string, body?: unknown): Promise<T> => {
    const response = await fetch(buildUrl(path), {
      method: 'PATCH',
      headers: buildHeaders(),
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
    return handleResponse<T>(response)
  },

  delete: async (path: string): Promise<void> => {
    const response = await fetch(buildUrl(path), {
      method: 'DELETE',
      headers: buildHeaders(),
    })
    await handleResponse<void>(response)
  },
}
