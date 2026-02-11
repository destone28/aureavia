import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/authStore';
import { useEffect } from 'react';

// Common
import { ToastContainer } from './components/common/ToastContainer';

// Driver pages
import LoginPage from './pages/driver/LoginPage';
import TwoFactorPage from './pages/driver/TwoFactorPage';
import RidesListPage from './pages/driver/RidesListPage';
import RideDetailPage from './pages/driver/RideDetailPage';
import ProfilePage from './pages/driver/ProfilePage';

// Admin pages
import AdminLoginPage from './pages/admin/AdminLoginPage';
import AdminTwoFactorPage from './pages/admin/AdminTwoFactorPage';
import DashboardPage from './pages/admin/DashboardPage';
import AddDriverPage from './pages/admin/AddDriverPage';
import AddPartnerPage from './pages/admin/AddPartnerPage';
import SettingsPage from './pages/admin/SettingsPage';

// Common pages
import ForgotPasswordPage from './pages/common/ForgotPasswordPage';
import ResetPasswordPage from './pages/common/ResetPasswordPage';

// Protected route component
function ProtectedRoute({ children, allowedRoles }: { children: React.ReactNode; allowedRoles?: string[] }) {
  const { isAuthenticated, user } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}

function App() {
  const { loadUser, isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated) {
      loadUser();
    }
  }, [isAuthenticated, loadUser]);

  return (
    <BrowserRouter>
      <ToastContainer />
      <Routes>
        {/* Driver routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/verify-2fa" element={<TwoFactorPage />} />
        <Route path="/rides" element={
          <ProtectedRoute><RidesListPage /></ProtectedRoute>
        } />
        <Route path="/rides/:id" element={
          <ProtectedRoute><RideDetailPage /></ProtectedRoute>
        } />
        <Route path="/profile" element={
          <ProtectedRoute><ProfilePage /></ProtectedRoute>
        } />

        {/* Admin routes */}
        <Route path="/admin/login" element={<AdminLoginPage />} />
        <Route path="/admin/verify-2fa" element={<AdminTwoFactorPage />} />
        <Route path="/admin/dashboard" element={
          <ProtectedRoute allowedRoles={['admin', 'assistant', 'finance']}>
            <DashboardPage />
          </ProtectedRoute>
        } />
        <Route path="/admin/add-driver" element={
          <ProtectedRoute allowedRoles={['admin']}>
            <AddDriverPage />
          </ProtectedRoute>
        } />
        <Route path="/admin/add-partner" element={
          <ProtectedRoute allowedRoles={['admin']}>
            <AddPartnerPage />
          </ProtectedRoute>
        } />
        <Route path="/admin/settings" element={
          <ProtectedRoute allowedRoles={['admin']}>
            <SettingsPage />
          </ProtectedRoute>
        } />

        {/* Password reset */}
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />

        {/* Default redirect */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
