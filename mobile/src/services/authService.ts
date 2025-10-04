/**
 * Auth Service - Handles authentication for ArxOS Mobile
 * Connects to ArxOS backend mobile API endpoints
 */

import { Logger } from '../utils/Logger';
import { axios } from 'axios';

// API Configuration
const API_BASE_URL = __DEV__ 
  ? 'http://localhost:8080/api/v1/mobile' 
  : 'https://api.arxos.com/v1/mobile';

export interface User {
  id: string;
  username: string;
  email: string;
  role: string;
  permissions: string[];
  organization_id?: string;
  full_name?: string;
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
  full_name?: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

export interface AuthResponse {
  user: User;
  tokens: AuthTokens;
}

export interface RefreshTokenResponse {
  tokens: AuthTokens;
}

export class AuthService {
  private logger: Logger;
  private currentUser: User | null = null;

  constructor() {


    this.logger = new Logger('AuthService');
  }

  /**
   * User authentication and management
   */
  getCurrentUser(): User | null {
    return this.currentUser;
  }

  setCurrentUser(user: User): void {
    this.currentUser = user;
  }

  isAuthenticated(): boolean {
    return this.currentUser !== null;
  }

  /**
   * Login
   */
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    try {
      this.logger.info('Attempting login', { username: credentials.username });
      
      const response = await axios.post(`${API_BASE_URL}/auth/login`, credentials);
      
      if (response.status === 200 && response.data) {
        const authResponse: AuthResponse = {
          user: response.data.user,
          tokens: response.data.tokens
        };
        
        this.setCurrentUser(authResponse.user);
        this.logger.info('Login successful', { user: authResponse.user.id });
        
        return authResponse;
      } else {
        throw new Error('Invalid response format');
      }
    } catch (error: any) {
      this.logger.error('Login failed', error);
      throw new Error(error.response?.data?.message || 'Login failed');
    }
  }

  /**
   * Register new user
   */
  async register(credentials: RegisterCredentials): Promise<AuthResponse> {
    try {
      this.logger.info('Attempting registration', { email: credentials.email });
      
      const response = await axios.post(`${API_BASE_URL}/auth/register`, credentials);
      
      if (response.status === 201 && response.data) {
        const authResponse: AuthResponse = {
          user: response.data.user,
          tokens: response.data.tokens
        };
        
        this.setCurrentUser(authResponse.user);
        this.logger.info('Registration successful', { user: authResponse.user.id });
        
        return authResponse;
      } else {
        throw new Error('Invalid response format');
      }
    } catch (error: any) {
      this.logger.error('Registration failed', error);
      throw new Error(error.response?.data?.message || 'Registration failed');
    }
  }

  /**
   * Refresh access token
   */
  async refreshToken(refreshToken: string): Promise<RefreshTokenResponse> {
    try {
      this.logger.info('Refreshing token');
      
      const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
        refresh_token: refreshToken
      });
      
      if (response.status === 200 && response.data) {
        const refreshResponse: RefreshTokenResponse = {
          tokens: response.data.tokens
        };
        
        this.logger.info('Token refresh successful');
        return refreshResponse;
      } else {
        throw new Error('Invalid response format');
      }
    } catch (error: any) {
      this.logger.error('Token refresh failed', error);
      throw new Error(error.response?.data?.message || 'Token refresh failed');
    }
  }

  /**
   * Get user profile
   */
  async getProfile(accessToken: string): Promise<User> {
    try {
      this.logger.info('Fetching user profile');
      
      const response = await axios.get(`${API_BASE_URL}/auth/profile`, {
        headers: {
          Authorization: `Bearer ${accessToken}`
        }
      });
      
      if (response.status === 200 && response.data) {
        const user: User = response.data.user;
        this.setCurrentUser(user);
        
        this.logger.info('Profile fetch successful', { user: user.id });
        return user;
      } else {
        throw new Error('Invalid response format');
      }
    } catch (error: any) {
      this.logger.error('Profile fetch failed', error);
      throw new Error(error.response?.data?.message || 'Profile fetch failed');
    }
  }

  /**
   * Logout
   */
  async logout(accessToken: string): Promise<void> {
    try {
      this.logger.info('Logging out user');
      
      await axios.post(`${API_BASE_URL}/auth/logout`, {}, {
        headers: {
          Authorization: `Bearer ${accessToken}`
        }
      });
      
      this.currentUser = null;
      this.logger.info('Logout successful');
    } catch (error: any) {
      this.logger.error('Logout failed', error);
      // Don't throw error for logout, just clear user
      this.currentUser = null;
    }
  }

  /**
   * Check authentication status
   */
  async checkAuthStatus(accessToken: string): Promise<AuthResponse | null> {
    try {
      const user = await this.getProfile(accessToken);
      
      if (user) {
        // Return a minimal auth response for status check
        return {
          user,
          tokens: {
            accessToken,
            refreshToken: '', // Not needed for status check
            expiresIn: 900 // 15 minutes default
          }
        };
      }
      
      return null;
    } catch (error: any) {
      this.logger.error('Auth status check failed', error);
      this.currentUser = null;
      return null;
    }
  }
}

// Export singleton instance
export const authService = new AuthService();