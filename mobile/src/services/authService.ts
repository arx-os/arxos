/**
 * Authentication Service
 * Handles user authentication and authorization
 */

import {apiService} from './apiService';
import {LoginCredentials, LoginResponse, User, AuthTokens} from '@/types/auth';
import {DeviceInfo} from '@/types/api';
import {Platform} from 'react-native';
import DeviceInfo from 'react-native-device-info';
import {logger} from '../utils/logger';
import {errorHandler, ErrorType, ErrorSeverity, createError} from '../utils/errorHandler';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Keychain from 'react-native-keychain';

class AuthService {
  private readonly TOKEN_KEY = 'auth_token';
  private readonly REFRESH_TOKEN_KEY = 'refresh_token';
  private readonly USER_KEY = 'user_data';
  
  /**
   * Login user with credentials
   */
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    try {
      logger.info('Attempting user login', { email: credentials.email }, 'AuthService');
      
      const deviceInfo: DeviceInfo = {
        platform: Platform.OS as 'ios' | 'android',
        version: Platform.Version.toString(),
        deviceId: await DeviceInfo.getUniqueId(),
        model: await DeviceInfo.getModel(),
        osVersion: await DeviceInfo.getSystemVersion(),
      };
      
      const response = await apiService.post<LoginResponse>('/auth/login', {
        ...credentials,
        deviceInfo,
      });
      
      // Store tokens securely
      await this.storeTokens(response.tokens);
      
      // Store user data
      if (response.user) {
        await AsyncStorage.setItem(this.USER_KEY, JSON.stringify(response.user));
      }
      
      logger.info('User login successful', { userId: response.user?.id }, 'AuthService');
      
      return response;
    } catch (error) {
      logger.error('Login failed', error, 'AuthService');
      throw errorHandler.handleError(
        createError(
          ErrorType.AUTHENTICATION,
          'Login failed',
          ErrorSeverity.HIGH,
          { component: 'AuthService', retryable: false }
        ),
        'AuthService'
      );
    }
  }
  
  /**
   * Logout user
   */
  async logout(): Promise<void> {
    try {
      logger.info('User logout initiated', {}, 'AuthService');
      
      await apiService.post('/auth/logout');
    } catch (error) {
      // Continue with logout even if API call fails
      logger.warn('Logout API call failed', error, 'AuthService');
    } finally {
      // Clear tokens from secure storage
      await this.clearTokens();
      
      logger.info('User logout completed', {}, 'AuthService');
    }
  }
  
  /**
   * Refresh authentication token
   */
  async refreshToken(): Promise<AuthTokens> {
    const response = await apiService.post<AuthTokens>('/auth/refresh');
    return response;
  }
  
  /**
   * Check current authentication status
   */
  async checkAuthStatus(): Promise<LoginResponse> {
    const response = await apiService.get<LoginResponse>('/auth/status');
    return response;
  }
  
  /**
   * Register new user
   */
  async register(credentials: {
    username: string;
    email: string;
    password: string;
    fullName?: string;
    organizationId?: string;
  }): Promise<LoginResponse> {
    const deviceInfo: DeviceInfo = {
      platform: Platform.OS as 'ios' | 'android',
      version: Platform.Version.toString(),
      deviceId: await DeviceInfo.getUniqueId(),
      model: await DeviceInfo.getModel(),
      osVersion: await DeviceInfo.getSystemVersion(),
    };
    
    const response = await apiService.post<LoginResponse>('/auth/register', {
      ...credentials,
      deviceInfo,
    });
    
    return response;
  }
  
  /**
   * Change password
   */
  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await apiService.post('/auth/change-password', {
      currentPassword,
      newPassword,
    });
  }
  
  /**
   * Reset password
   */
  async resetPassword(email: string): Promise<void> {
    await apiService.post('/auth/reset-password', {email});
  }
  
  /**
   * Verify email
   */
  async verifyEmail(token: string): Promise<void> {
    await apiService.post('/auth/verify-email', {token});
  }
  
  /**
   * Get user profile
   */
  async getUserProfile(): Promise<User> {
    const response = await apiService.get<User>('/auth/profile');
    return response;
  }
  
  /**
   * Update user profile
   */
  async updateUserProfile(updates: Partial<User>): Promise<User> {
    const response = await apiService.patch<User>('/auth/profile', updates);
    return response;
  }
  
  /**
   * Enable biometric authentication
   */
  async enableBiometric(): Promise<void> {
    await apiService.post('/auth/biometric/enable');
  }
  
  /**
   * Disable biometric authentication
   */
  async disableBiometric(): Promise<void> {
    await apiService.post('/auth/biometric/disable');
  }
  
  /**
   * Check if biometric is supported
   */
  async checkBiometricSupport(): Promise<{supported: boolean; type: string}> {
    const response = await apiService.get<{supported: boolean; type: string}>('/auth/biometric/support');
    return response;
  }
  
  /**
   * Store tokens securely
   */
  private async storeTokens(tokens: AuthTokens): Promise<void> {
    try {
      // Store access token in keychain
      await Keychain.setInternetCredentials(
        this.TOKEN_KEY,
        'arxos_user',
        tokens.accessToken
      );
      
      // Store refresh token in keychain
      await Keychain.setInternetCredentials(
        this.REFRESH_TOKEN_KEY,
        'arxos_user',
        tokens.refreshToken
      );
      
      logger.debug('Tokens stored securely', {}, 'AuthService');
    } catch (error) {
      logger.error('Failed to store tokens', error, 'AuthService');
      throw error;
    }
  }
  
  /**
   * Get access token from keychain
   */
  private async getAccessToken(): Promise<string | null> {
    try {
      const credentials = await Keychain.getInternetCredentials(this.TOKEN_KEY);
      return credentials ? credentials.password : null;
    } catch (error) {
      logger.error('Failed to get access token', error, 'AuthService');
      return null;
    }
  }
  
  /**
   * Get refresh token from keychain
   */
  private async getRefreshToken(): Promise<string | null> {
    try {
      const credentials = await Keychain.getInternetCredentials(this.REFRESH_TOKEN_KEY);
      return credentials ? credentials.password : null;
    } catch (error) {
      logger.error('Failed to get refresh token', error, 'AuthService');
      return null;
    }
  }
  
  /**
   * Clear tokens from storage
   */
  private async clearTokens(): Promise<void> {
    try {
      await Keychain.resetInternetCredentials(this.TOKEN_KEY);
      await Keychain.resetInternetCredentials(this.REFRESH_TOKEN_KEY);
      await AsyncStorage.removeItem(this.USER_KEY);
      
      logger.debug('Tokens cleared from storage', {}, 'AuthService');
    } catch (error) {
      logger.error('Failed to clear tokens', error, 'AuthService');
    }
  }
  
  /**
   * Check if user is authenticated
   */
  async isAuthenticated(): Promise<boolean> {
    try {
      const token = await this.getAccessToken();
      const refreshToken = await this.getRefreshToken();
      
      return !!(token && refreshToken);
    } catch (error) {
      logger.error('Authentication check failed', error, 'AuthService');
      return false;
    }
  }
  
  /**
   * Initialize authentication state
   */
  async initializeAuth(): Promise<void> {
    try {
      const token = await this.getAccessToken();
      const refreshToken = await this.getRefreshToken();
      const userData = await AsyncStorage.getItem(this.USER_KEY);
      
      if (token && refreshToken && userData) {
        const user = JSON.parse(userData);
        logger.info('Authentication state restored', { userId: user.id }, 'AuthService');
      }
    } catch (error) {
      logger.error('Failed to initialize authentication', error, 'AuthService');
    }
  }
}

export const authService = new AuthService();
