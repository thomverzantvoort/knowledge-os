import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { AppLayout } from '@/components/AppLayout'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { AuthProvider } from '@/lib/auth'
import { HistoryPage } from '@/pages/HistoryPage'
import { LoginPage } from '@/pages/LoginPage'

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route path="/history" element={<HistoryPage />} />
            </Route>
          </Route>
          <Route path="/library" element={<Navigate to="/history" replace />} />
          <Route path="/" element={<Navigate to="/history" replace />} />
          <Route path="*" element={<Navigate to="/history" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
