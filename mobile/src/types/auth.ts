/**
 * Authentication-related type definitions
 */

export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  expiresAt: number | null;
  isLoading: boolean;
  error: string | null;
}

export interface User {
  id: string;
  username: string;
  email: string;
  role: string;
  permissions: string[];
  organizationId?: string;
  fullName?: string;
  avatar?: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterCredentials {
  username: string;
  email: string;
  password: string;
  fullName?: string;
  organizationId?: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

export interface AuthError {
  code: string;
  message: string;
  details?: any;
}

export interface BiometricAuth {
  isSupported: boolean;
  isEnabled: boolean;
  type: 'fingerprint' | 'face' | 'iris' | null;
}

export interface SecuritySettings {
  biometricEnabled: boolean;
  autoLockTimeout: number;
  requirePasswordOnStartup: boolean;
  sessionTimeout: number;
}
