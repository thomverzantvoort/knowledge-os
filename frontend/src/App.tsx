import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { AppLayout } from '@/components/AppLayout'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { AuthProvider } from '@/lib/auth'
import { HistoryPage } from '@/pages/HistoryPage'
import { InboxPage } from '@/pages/InboxPage'
import { LibraryDetailPage } from '@/pages/LibraryDetailPage'
import { LibraryPage } from '@/pages/LibraryPage'
import { LoginPage } from '@/pages/LoginPage'

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route path="/inbox" element={<InboxPage />} />
              <Route path="/library" element={<LibraryPage />} />
              <Route path="/library/:id" element={<LibraryDetailPage />} />
              <Route path="/history" element={<HistoryPage />} />
            </Route>
          </Route>
          <Route path="/" element={<Navigate to="/inbox" replace />} />
          <Route path="*" element={<Navigate to="/inbox" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
