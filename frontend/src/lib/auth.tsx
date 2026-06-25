import {
  useCallback,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import {
  clearStoredToken,
  getStoredToken,
  login as apiLogin,
  setStoredToken,
} from '@/lib/api'
import { AuthContext, type AuthContextValue } from '@/lib/auth-context'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => getStoredToken())

  const login = useCallback(async (username: string, password: string) => {
    const response = await apiLogin(username, password)
    setStoredToken(response.access_token)
    setToken(response.access_token)
  }, [])

  const logout = useCallback(() => {
    clearStoredToken()
    setToken(null)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      isAuthenticated: token !== null,
      login,
      logout,
    }),
    [token, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
