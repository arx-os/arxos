import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import axios, { AxiosInstance } from 'axios';

// Types
export interface User {
  user_id: string;
  username: string;
  email: string;
  role: 'admin' | 'editor' | 'viewer';
  permissions: string[];
  created_at: string;
  last_login: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

export interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  apiClient: AxiosInstance;
}

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// API client configuration
const createApiClient = (token?: string): AxiosInstance => {
  const client = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor to add auth token
  client.interceptors.request.use(
    (config) => {
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor to handle token refresh
  client.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;

      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;

        try {
          const refreshToken = localStorage.getItem('refresh_token');
          if (refreshToken) {
            const response = await axios.post('/auth/refresh', {
              refresh_token: refreshToken,
            });
            
            const { access_token } = response.data;
            localStorage.setItem('access_token', access_token);
            
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
            return client(originalRequest);
          }
        } catch (refreshError) {
          // Refresh failed, redirect to login
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }

      return Promise.reject(error);
    }
  );

  return client;
};

// Auth Provider Component
export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [apiClient, setApiClient] = useState<AxiosInstance>(() => createApiClient());
  const navigate = useNavigate();

  // Initialize auth state
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const token = localStorage.getItem('access_token');
        if (token) {
          const client = createApiClient(token);
          setApiClient(client);
          
          // Verify token and get user info
          const response = await client.get('/auth/me');
          setUser(response.data);
        }
      } catch (error) {
        console.error('Auth initialization failed:', error);
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();
  }, []);

  // Login function
  const login = useCallback(async (credentials: LoginCredentials) => {
    try {
      setLoading(true);
      
      const response = await apiClient.post('/auth/login', credentials);
      const { access_token, refresh_token, user: userData } = response.data;
      
      // Store tokens
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      
      // Update API client with new token
      const newClient = createApiClient(access_token);
      setApiClient(newClient);
      
      // Set user
      setUser(userData);
      
      toast.success(`Welcome back, ${userData.username}!`);
      navigate('/');
      
    } catch (error: any) {
      console.error('Login failed:', error);
      
      const errorMessage = error.response?.data?.message || 'Login failed. Please try again.';
      toast.error(errorMessage);
      
      throw error;
    } finally {
      setLoading(false);
    }
  }, [apiClient, navigate]);

  // Logout function
  const logout = useCallback(async () => {
    try {
      // Call logout endpoint if available
      await apiClient.post('/auth/logout');
    } catch (error) {
      console.error('Logout API call failed:', error);
    } finally {
      // Clear local storage
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      
      // Reset state
      setUser(null);
      setApiClient(createApiClient());
      
      toast.success('Logged out successfully');
      navigate('/login');
    }
  }, [apiClient, navigate]);

  // Refresh token function
  const refreshToken = useCallback(async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await axios.post(`${apiClient.defaults.baseURL}/auth/refresh`, {
        refresh_token: refreshToken,
      });
      
      const { access_token } = response.data;
      localStorage.setItem('access_token', access_token);
      
      // Update API client
      const newClient = createApiClient(access_token);
      setApiClient(newClient);
      
      return access_token;
    } catch (error) {
      console.error('Token refresh failed:', error);
      await logout();
      throw error;
    }
  }, [apiClient, logout]);

  // Check if user has permission
  const hasPermission = useCallback((permission: string): boolean => {
    if (!user) return false;
    return user.permissions.includes(permission) || user.role === 'admin';
  }, [user]);

  // Check if user has role
  const hasRole = useCallback((role: string): boolean => {
    if (!user) return false;
    return user.role === role || user.role === 'admin';
  }, [user]);

  const value: AuthContextType = {
    user,
    loading,
    isAuthenticated: !!user,
    login,
    logout,
    refreshToken,
    apiClient,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook to use auth context
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Permission hook
export const usePermission = (permission: string): boolean => {
  const { user } = useAuth();
  if (!user) return false;
  return user.permissions.includes(permission) || user.role === 'admin';
};

// Role hook
export const useRole = (role: string): boolean => {
  const { user } = useAuth();
  if (!user) return false;
  return user.role === role || user.role === 'admin';
};

// Protected component wrapper
export const withPermission = <P extends object>(
  Component: React.ComponentType<P>,
  permission: string
): React.FC<P> => {
  return (props: P) => {
    const hasPermission = usePermission(permission);
    
    if (!hasPermission) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-red-600 mb-2">Access Denied</h2>
            <p className="text-gray-600">You don't have permission to access this resource.</p>
          </div>
        </div>
      );
    }
    
    return <Component {...props} />;
  };
};

// Protected component wrapper for roles
export const withRole = <P extends object>(
  Component: React.ComponentType<P>,
  role: string
): React.FC<P> => {
  return (props: P) => {
    const hasRole = useRole(role);
    
    if (!hasRole) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-red-600 mb-2">Access Denied</h2>
            <p className="text-gray-600">You don't have the required role to access this resource.</p>
          </div>
        </div>
      );
    }
    
    return <Component {...props} />;
  };
}; 