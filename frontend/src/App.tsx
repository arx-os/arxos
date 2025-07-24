import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { ErrorBoundary } from 'react-error-boundary';

// Components
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { WebSocketProvider } from './contexts/WebSocketContext';
import { CollaborationProvider } from './contexts/CollaborationContext';
import { CanvasProvider } from './contexts/CanvasContext';

// Pages
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import CanvasPage from './pages/CanvasPage';
import SettingsPage from './pages/SettingsPage';
import ErrorPage from './pages/ErrorPage';

// Layout
import Layout from './components/Layout/Layout';
import LoadingSpinner from './components/UI/LoadingSpinner';

// Styles
import './styles/globals.css';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
    },
  },
});

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

// Error Fallback Component
const ErrorFallback: React.FC<{ error: Error; resetErrorBoundary: () => void }> = ({
  error,
  resetErrorBoundary,
}) => {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold text-red-600 mb-4">Something went wrong</h2>
        <p className="text-gray-600 mb-4">
          An unexpected error occurred. Please try refreshing the page.
        </p>
        <details className="mb-4">
          <summary className="cursor-pointer text-sm text-gray-500">Error details</summary>
          <pre className="mt-2 text-xs bg-gray-100 p-2 rounded overflow-auto">
            {error.message}
          </pre>
        </details>
        <button
          onClick={resetErrorBoundary}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 transition-colors"
        >
          Try again
        </button>
      </div>
    </div>
  );
};

// Main App Component
const App: React.FC = () => {
  return (
    <ErrorBoundary FallbackComponent={ErrorFallback}>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <WebSocketProvider>
            <CollaborationProvider>
              <CanvasProvider>
                <Router>
                  <div className="min-h-screen bg-gray-50">
                    <Routes>
                      {/* Public Routes */}
                      <Route path="/login" element={<LoginPage />} />
                      
                      {/* Protected Routes */}
                      <Route
                        path="/"
                        element={
                          <ProtectedRoute>
                            <Layout>
                              <DashboardPage />
                            </Layout>
                          </ProtectedRoute>
                        }
                      />
                      
                      <Route
                        path="/canvas/:canvasId"
                        element={
                          <ProtectedRoute>
                            <Layout>
                              <CanvasPage />
                            </Layout>
                          </ProtectedRoute>
                        }
                      />
                      
                      <Route
                        path="/settings"
                        element={
                          <ProtectedRoute>
                            <Layout>
                              <SettingsPage />
                            </Layout>
                          </ProtectedRoute>
                        }
                      />
                      
                      {/* Error Routes */}
                      <Route path="/error" element={<ErrorPage />} />
                      <Route path="*" element={<Navigate to="/" replace />} />
                    </Routes>
                    
                    {/* Global Toast Notifications */}
                    <Toaster
                      position="top-right"
                      toastOptions={{
                        duration: 4000,
                        style: {
                          background: '#363636',
                          color: '#fff',
                        },
                        success: {
                          duration: 3000,
                          iconTheme: {
                            primary: '#10b981',
                            secondary: '#fff',
                          },
                        },
                        error: {
                          duration: 5000,
                          iconTheme: {
                            primary: '#ef4444',
                            secondary: '#fff',
                          },
                        },
                      }}
                    />
                  </div>
                </Router>
              </CanvasProvider>
            </CollaborationProvider>
          </WebSocketProvider>
        </AuthProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
};

export default App; 