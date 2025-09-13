import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import apiClient from '../services/api/client';

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  orgId?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  refreshToken: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

const TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const USER_KEY = '@arxos_user';

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    checkAuthState();
  }, []);

  const checkAuthState = async () => {
    try {
      const [storedToken, storedUser] = await Promise.all([
        AsyncStorage.getItem(TOKEN_KEY),
        AsyncStorage.getItem(USER_KEY)
      ]);

      if (storedToken && storedUser) {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
        
        // Token is automatically handled by API client interceptors
        
        // Validate token with server
        try {
          await apiClient.get('/auth/validate');
        } catch (error) {
          // Token is invalid, try to refresh
          await refreshToken();
        }
      }
    } catch (error) {
      console.error('Error checking auth state:', error);
      await logout();
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string): Promise<void> => {
    setIsLoading(true);
    try {
      const response = await apiClient.post('/auth/login', {
        email,
        password
      });

      const { accessToken, refreshToken: newRefreshToken, user: userData } = response.data;

      // Store tokens and user data
      await Promise.all([
        AsyncStorage.setItem(TOKEN_KEY, accessToken),
        AsyncStorage.setItem(REFRESH_TOKEN_KEY, newRefreshToken),
        AsyncStorage.setItem(USER_KEY, JSON.stringify(userData))
      ]);

      setToken(accessToken);
      setUser(userData);
      
      // Token is automatically handled by API client interceptors
    } catch (error) {
      console.error('Login error:', error);
      throw new Error('Invalid email or password');
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (email: string, password: string, name: string): Promise<void> => {
    setIsLoading(true);
    try {
      const response = await apiClient.post('/auth/register', {
        email,
        password,
        name
      });

      const { accessToken, refreshToken: newRefreshToken, user: userData } = response.data;

      // Store tokens and user data
      await Promise.all([
        AsyncStorage.setItem(TOKEN_KEY, accessToken),
        AsyncStorage.setItem(REFRESH_TOKEN_KEY, newRefreshToken),
        AsyncStorage.setItem(USER_KEY, JSON.stringify(userData))
      ]);

      setToken(accessToken);
      setUser(userData);
      
      // Token is automatically handled by API client interceptors
    } catch (error) {
      console.error('Registration error:', error);
      throw new Error('Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  const refreshToken = async (): Promise<void> => {
    try {
      const storedRefreshToken = await AsyncStorage.getItem(REFRESH_TOKEN_KEY);
      if (!storedRefreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await apiClient.post('/auth/refresh', {
        refreshToken: storedRefreshToken
      });

      const { accessToken, refreshToken: newRefreshToken, user: userData } = response.data;

      // Store new tokens
      await Promise.all([
        AsyncStorage.setItem(TOKEN_KEY, accessToken),
        AsyncStorage.setItem(REFRESH_TOKEN_KEY, newRefreshToken),
        AsyncStorage.setItem(USER_KEY, JSON.stringify(userData))
      ]);

      setToken(accessToken);
      setUser(userData);
      
      // Token is automatically handled by API client interceptors
    } catch (error) {
      console.error('Token refresh error:', error);
      await logout();
      throw new Error('Session expired');
    }
  };

  const logout = async (): Promise<void> => {
    try {
      // Notify server of logout
      if (token) {
        await apiClient.post('/auth/logout');
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local storage
      await Promise.all([
        AsyncStorage.removeItem(TOKEN_KEY),
        AsyncStorage.removeItem(REFRESH_TOKEN_KEY),
        AsyncStorage.removeItem(USER_KEY)
      ]);

      setToken(null);
      setUser(null);
      
      // Token cleanup is automatically handled by API client interceptors
    }
  };

  const value: AuthContextType = {
    user,
    token,
    isLoading,
    isAuthenticated: !!user && !!token,
    login,
    logout,
    register,
    refreshToken
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};