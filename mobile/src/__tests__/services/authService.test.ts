/**
 * AuthService Tests
 * Unit tests for authentication service
 */

import {authService} from '../../services/authService';
import {apiService} from '../../services/apiService';
import {logger} from "../../utils/logger";
import {errorHandler} from '../../utils/errorHandler';
import * as Keychain from 'react-native-keychain';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Mock dependencies
jest.mock('../../services/apiService');
jest.mock('axios');
jest.mock('../../utils/logger');
jest.mock('../../utils/errorHandler');
jest.mock('react-native-keychain');
jest.mock('@react-native-async-storage/async-storage');

const mockAxios = require('axios');
const mockApiService = apiService as jest.Mocked<typeof apiService>;
const mockLogger = {
  info: jest.fn(),
  error: jest.fn(),
  warn: jest.fn(),
  debug: jest.fn(),
} as any;
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
        username: 'test@example.com',
        password: 'password123',
      };
      
      const mockResponse = {
        user: { id: '1', email: 'test@example.com', name: 'Test User' },
        tokens: {
          accessToken: 'access-token',
          refreshToken: 'refresh-token',
        },
      };

      // Mock axios.post directly since AuthService uses axios
      mockAxios.post.mockResolvedValue(mockResponse);
      mockKeychain.setInternetCredentials.mockResolvedValue({} as any);
      mockAsyncStorage.setItem.mockResolvedValue(undefined);

      // Act
      const result = await authService.login(credentials);

      // Assert
      expect(result).toEqual(mockResponse);
      expect(mockAxios.post).toHaveBeenCalledWith('http://localhost:8080/api/v1/mobile/auth/login', expect.objectContaining({
        username: credentials.username,
        password: credentials.password,
      }));
      expect(mockKeychain.setInternetCredentials).toHaveBeenCalledTimes(2);
      expect(mockAsyncStorage.setItem).toHaveBeenCalledWith('user_data', JSON.stringify(mockResponse.user));
      expect(mockLogger.info).toHaveBeenCalledWith('User login successful', { userId: '1' }, 'AuthService');
    });

    it('should handle login failure', async () => {
      // Arrange
      const credentials = {
        username: 'test@example.com',
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
      await authService.logout('test-access-token');

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
      await authService.logout('test-access-token');

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
        .mockResolvedValueOnce({ 
          server: 'arxos.com',
          username: 'user',
          password: 'access-token',
          service: 'access-token',
          storage: 'keychain'
        })
        .mockResolvedValueOnce({ 
          server: 'arxos.com',
          username: 'user',
          password: 'refresh-token',
          service: 'refresh-token',
          storage: 'keychain'
        });

      // Act
      const result = await authService.isAuthenticated();

      // Assert
      expect(result).toBe(true);
    });

    it('should return false when user is not authenticated', async () => {
      // Arrange
      mockKeychain.getInternetCredentials
        .mockResolvedValueOnce(false)
        .mockResolvedValueOnce(false);

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

  // TODO: Add tests for initializeAuth when method is implemented
  // describe('initializeAuth', () => {
  //   it('should initialize authentication state successfully', async () => {
  //     // Test implementation when method is available
  //   });
  // });

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
      mockKeychain.setInternetCredentials.mockResolvedValue({} as any);
      mockAsyncStorage.setItem.mockResolvedValue(undefined);

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

  // TODO: Add tests for changePassword when method is implemented
  // describe('changePassword', () => {
  //   it('should change password successfully', async () => {
  //     // Test implementation when method is available
  //   });
  // });

  // TODO: Add tests for resetPassword when method is implemented
  // describe('resetPassword', () => {
  //   it('should reset password successfully', async () => {
  //     // Test implementation when method is available
  //   });
  // });

  describe('getProfile', () => {
    it('should get user profile successfully', async () => {
      // Arrange
      const mockProfile = { id: '1', email: 'test@example.com', name: 'Test User' };
      mockApiService.get.mockResolvedValue(mockProfile);
      mockAsyncStorage.setItem.mockResolvedValue();

      // Act
      const result = await authService.getProfile('access-token');

      // Assert
      expect(result).toEqual(mockProfile);
      expect(mockApiService.get).toHaveBeenCalledWith('/auth/profile');
      expect(mockAsyncStorage.setItem).toHaveBeenCalledWith('user_data', JSON.stringify(mockProfile));
    });
  });
});
