/**
 * AuthService Tests
 * Unit tests for authentication service
 */

import {authService} from '../../services/authService';
import {apiService} from '../../services/apiService';
import {logger} from '../../utils/logger';
import {errorHandler} from '../../utils/errorHandler';
import * as Keychain from 'react-native-keychain';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Mock dependencies
jest.mock('../../services/apiService');
jest.mock('../../utils/logger');
jest.mock('../../utils/errorHandler');
jest.mock('react-native-keychain');
jest.mock('@react-native-async-storage/async-storage');

const mockApiService = apiService as jest.Mocked<typeof apiService>;
const mockLogger = logger as jest.Mocked<typeof logger>;
const mockErrorHandler = errorHandler as jest.Mocked<typeof errorHandler>;
const mockKeychain = Keychain as jest.Mocked<typeof Keychain>;
const mockAsyncStorage = AsyncStorage as jest.Mocked<typeof AsyncStorage>;

describe('AuthService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('login', () => {
    it('should login user successfully', async () => {
      // Arrange
      const credentials = {
        email: 'test@example.com',
        password: 'password123',
      };
      
      const mockResponse = {
        user: { id: '1', email: 'test@example.com', name: 'Test User' },
        tokens: {
          accessToken: 'access-token',
          refreshToken: 'refresh-token',
        },
      };

      mockApiService.post.mockResolvedValue(mockResponse);
      mockKeychain.setInternetCredentials.mockResolvedValue();
      mockAsyncStorage.setItem.mockResolvedValue();

      // Act
      const result = await authService.login(credentials);

      // Assert
      expect(result).toEqual(mockResponse);
      expect(mockApiService.post).toHaveBeenCalledWith('/auth/login', expect.objectContaining({
        email: credentials.email,
        password: credentials.password,
        deviceInfo: expect.any(Object),
      }));
      expect(mockKeychain.setInternetCredentials).toHaveBeenCalledTimes(2);
      expect(mockAsyncStorage.setItem).toHaveBeenCalledWith('user_data', JSON.stringify(mockResponse.user));
      expect(mockLogger.info).toHaveBeenCalledWith('User login successful', { userId: '1' }, 'AuthService');
    });

    it('should handle login failure', async () => {
      // Arrange
      const credentials = {
        email: 'test@example.com',
        password: 'wrongpassword',
      };
      
      const error = new Error('Invalid credentials');
      mockApiService.post.mockRejectedValue(error);

      // Act & Assert
      await expect(authService.login(credentials)).rejects.toThrow();
      expect(mockErrorHandler.handleError).toHaveBeenCalled();
      expect(mockLogger.error).toHaveBeenCalledWith('Login failed', error, 'AuthService');
    });
  });

  describe('logout', () => {
    it('should logout user successfully', async () => {
      // Arrange
      mockApiService.post.mockResolvedValue({});
      mockKeychain.resetInternetCredentials.mockResolvedValue();
      mockAsyncStorage.removeItem.mockResolvedValue();

      // Act
      await authService.logout();

      // Assert
      expect(mockApiService.post).toHaveBeenCalledWith('/auth/logout');
      expect(mockKeychain.resetInternetCredentials).toHaveBeenCalledTimes(2);
      expect(mockAsyncStorage.removeItem).toHaveBeenCalledWith('user_data');
      expect(mockLogger.info).toHaveBeenCalledWith('User logout completed', {}, 'AuthService');
    });

    it('should continue logout even if API call fails', async () => {
      // Arrange
      const error = new Error('Network error');
      mockApiService.post.mockRejectedValue(error);
      mockKeychain.resetInternetCredentials.mockResolvedValue();
      mockAsyncStorage.removeItem.mockResolvedValue();

      // Act
      await authService.logout();

      // Assert
      expect(mockLogger.warn).toHaveBeenCalledWith('Logout API call failed', error, 'AuthService');
      expect(mockKeychain.resetInternetCredentials).toHaveBeenCalledTimes(2);
      expect(mockAsyncStorage.removeItem).toHaveBeenCalledWith('user_data');
    });
  });

  describe('isAuthenticated', () => {
    it('should return true when user is authenticated', async () => {
      // Arrange
      mockKeychain.getInternetCredentials
        .mockResolvedValueOnce({ password: 'access-token' })
        .mockResolvedValueOnce({ password: 'refresh-token' });

      // Act
      const result = await authService.isAuthenticated();

      // Assert
      expect(result).toBe(true);
    });

    it('should return false when user is not authenticated', async () => {
      // Arrange
      mockKeychain.getInternetCredentials
        .mockResolvedValueOnce(null)
        .mockResolvedValueOnce(null);

      // Act
      const result = await authService.isAuthenticated();

      // Assert
      expect(result).toBe(false);
    });

    it('should return false when keychain access fails', async () => {
      // Arrange
      const error = new Error('Keychain error');
      mockKeychain.getInternetCredentials.mockRejectedValue(error);

      // Act
      const result = await authService.isAuthenticated();

      // Assert
      expect(result).toBe(false);
      expect(mockLogger.error).toHaveBeenCalledWith('Authentication check failed', error, 'AuthService');
    });
  });

  describe('initializeAuth', () => {
    it('should initialize authentication state successfully', async () => {
      // Arrange
      const mockUser = { id: '1', email: 'test@example.com', name: 'Test User' };
      mockKeychain.getInternetCredentials
        .mockResolvedValueOnce({ password: 'access-token' })
        .mockResolvedValueOnce({ password: 'refresh-token' });
      mockAsyncStorage.getItem.mockResolvedValue(JSON.stringify(mockUser));

      // Act
      await authService.initializeAuth();

      // Assert
      expect(mockLogger.info).toHaveBeenCalledWith('Authentication state restored', { userId: '1' }, 'AuthService');
    });

    it('should handle initialization failure gracefully', async () => {
      // Arrange
      const error = new Error('Storage error');
      mockKeychain.getInternetCredentials.mockRejectedValue(error);

      // Act
      await authService.initializeAuth();

      // Assert
      expect(mockLogger.error).toHaveBeenCalledWith('Failed to initialize authentication', error, 'AuthService');
    });
  });

  describe('register', () => {
    it('should register user successfully', async () => {
      // Arrange
      const credentials = {
        username: 'testuser',
        email: 'test@example.com',
        password: 'password123',
        fullName: 'Test User',
      };
      
      const mockResponse = {
        user: { id: '1', email: 'test@example.com', name: 'Test User' },
        tokens: {
          accessToken: 'access-token',
          refreshToken: 'refresh-token',
        },
      };

      mockApiService.post.mockResolvedValue(mockResponse);
      mockKeychain.setInternetCredentials.mockResolvedValue();
      mockAsyncStorage.setItem.mockResolvedValue();

      // Act
      const result = await authService.register(credentials);

      // Assert
      expect(result).toEqual(mockResponse);
      expect(mockApiService.post).toHaveBeenCalledWith('/auth/register', expect.objectContaining({
        ...credentials,
        deviceInfo: expect.any(Object),
      }));
    });
  });

  describe('changePassword', () => {
    it('should change password successfully', async () => {
      // Arrange
      const currentPassword = 'oldpassword';
      const newPassword = 'newpassword';
      mockApiService.post.mockResolvedValue({});

      // Act
      await authService.changePassword(currentPassword, newPassword);

      // Assert
      expect(mockApiService.post).toHaveBeenCalledWith('/auth/change-password', {
        currentPassword,
        newPassword,
      });
      expect(mockLogger.info).toHaveBeenCalledWith('Password changed successfully', {}, 'AuthService');
    });
  });

  describe('resetPassword', () => {
    it('should reset password successfully', async () => {
      // Arrange
      const email = 'test@example.com';
      mockApiService.post.mockResolvedValue({});

      // Act
      await authService.resetPassword(email);

      // Assert
      expect(mockApiService.post).toHaveBeenCalledWith('/auth/reset-password', { email });
      expect(mockLogger.info).toHaveBeenCalledWith('Password reset request sent', { email }, 'AuthService');
    });
  });

  describe('getUserProfile', () => {
    it('should get user profile successfully', async () => {
      // Arrange
      const mockProfile = { id: '1', email: 'test@example.com', name: 'Test User' };
      mockApiService.get.mockResolvedValue(mockProfile);
      mockAsyncStorage.setItem.mockResolvedValue();

      // Act
      const result = await authService.getUserProfile();

      // Assert
      expect(result).toEqual(mockProfile);
      expect(mockApiService.get).toHaveBeenCalledWith('/auth/profile');
      expect(mockAsyncStorage.setItem).toHaveBeenCalledWith('user_data', JSON.stringify(mockProfile));
    });
  });
});
