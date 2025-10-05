/**
 * API Service
 * Centralized HTTP client for ArxOS Mobile
 * Connects to the main ArxOS backend API
 */

import axios, {AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError} from 'axios';
import {APIResponse, APIError} from '@/types/api';
import {store} from '@/store';
import {logout} from '@/store/slices/authSlice';
import {Logger} from "../utils/logger";
import {errorHandler, ErrorType, ErrorSeverity, createError} from '../utils/errorHandler';

// API Configuration
const API_BASE_URL = __DEV__ 
  ? 'http://localhost:8080/api/v1/mobile' 
  : 'https://api.arxos.com/v1/mobile';

const API_TIMEOUT = 30000; // 30 seconds

// Create logger instance
const logger = new Logger('ApiService');

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token to requests
    const state = store.getState();
    const token = state.auth.token;
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Add device info
    config.headers['X-Device-Platform'] = 'mobile';
    config.headers['X-Device-Type'] = 'react-native';
    
    // Log request in debug mode
    if (__DEV__) {
      logger.debug(`API Request: ${config.method?.toUpperCase()} ${config.url}`, {
        headers: config.headers,
        data: config.data,
      });
    }
    
    return config;
  },
  (error) => {
    logger.error('Request interceptor error', error as Error);
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response: AxiosResponse<APIResponse>) => {
    // Log response in debug mode
    if (__DEV__) {
      logger.debug(`API Response: ${response.status} ${response.config.url}`, {
        data: response.data,
      });
    }
    
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config;
    
    // Log error
    logger.error('API Response error', {
      status: error.response?.status,
      statusText: error.response?.statusText,
      url: error.config?.url,
      method: error.config?.method,
      data: error.response?.data,
    });
    
    // Handle 401 errors (unauthorized)
    if (error.response?.status === 401 && originalRequest && !(originalRequest as any)._retry) {
      (originalRequest as any)._retry = true;
      
      try {
        // Try to refresh token
        const state = store.getState();
        const refreshToken = state.auth.refreshToken;
        
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL.replace('/mobile', '')}/mobile/auth/refresh`, {
            refresh_token: refreshToken,
          });
          
          const {accessToken, refreshToken: newRefreshToken} = response.data.data;
          
          // Update tokens in store
          store.dispatch({
            type: 'auth/updateToken',
            payload: {
              accessToken,
              refreshToken: newRefreshToken,
              expiresIn: response.data.data.expiresIn,
            },
          });
          
          // Retry original request
          originalRequest.headers.Authorization = `Bearer ${accessToken}`;
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, logout user
        logger.error('Token refresh failed', refreshError as Error);
        store.dispatch(logout());
        return Promise.reject(refreshError);
      }
    }
    
    // Handle other errors
    const appError = errorHandler.handleError(
      createError(
        ErrorType.NETWORK,
        `API request failed: ${error.config?.url}`,
        ErrorSeverity.HIGH,
        { 
          component: 'ApiService', 
          retryable: (error.response?.status || 0) >= 500,
          details: {
            status: error.response?.status,
            statusText: error.response?.statusText,
            data: error.response?.data,
          }
        }
      ),
      'ApiService'
    );
    
    return Promise.reject(appError);
  }
);

// API Service class
export class ApiService {
  private client: AxiosInstance;
  private maxRetries: number = 3;
  private retryDelay: number = 1000;
  
  constructor() {
    this.client = apiClient;
  }
  
  private async retryRequest<T>(
    requestFn: () => Promise<AxiosResponse<APIResponse<T>>>,
    retryCount: number = 0
  ): Promise<AxiosResponse<APIResponse<T>>> {
    try {
      return await requestFn();
    } catch (error) {
      const axiosError = error as AxiosError;
      
      // Retry on network errors or 5xx server errors
      const shouldRetry = !axiosError.response || 
        (axiosError.response.status >= 500 && axiosError.response.status < 600);
      
      if (retryCount < this.maxRetries && shouldRetry) {
        logger.info(`Retrying request (attempt ${retryCount + 1}/${this.maxRetries})`, {
          url: axiosError.config?.url,
          status: axiosError.response?.status,
        });

        // Wait before retry with exponential backoff
        await new Promise(resolve => setTimeout(resolve, this.retryDelay * Math.pow(2, retryCount)));
        
        return this.retryRequest(requestFn, retryCount + 1);
      }
      
      throw error;
    }
  }
  
  // Generic HTTP methods with retry logic
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    try {
      const response = await this.retryRequest(() => this.client.get<APIResponse<T>>(url, config));
      return response.data.data;
    } catch (error) {
      throw error; // Error already handled by interceptor
    }
  }
  
  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    try {
      const response = await this.retryRequest(() => this.client.post<APIResponse<T>>(url, data, config));
      return response.data.data;
    } catch (error) {
      throw error; // Error already handled by interceptor
    }
  }
  
  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    try {
      const response = await this.retryRequest(() => this.client.put<APIResponse<T>>(url, data, config));
      return response.data.data;
    } catch (error) {
      throw error; // Error already handled by interceptor
    }
  }
  
  async patch<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    try {
      const response = await this.retryRequest(() => this.client.patch<APIResponse<T>>(url, data, config));
      return response.data.data;
    } catch (error) {
      throw error; // Error already handled by interceptor
    }
  }
  
  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    try {
      const response = await this.retryRequest(() => this.client.delete<APIResponse<T>>(url, config));
      return response.data.data;
    } catch (error) {
      throw error; // Error already handled by interceptor
    }
  }
  
  // File upload
  async uploadFile<T>(url: string, file: FormData, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<APIResponse<T>>(url, file, {
      ...config,
      headers: {
        ...config?.headers,
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data.data;
  }
  
  // Health check
  async healthCheck(): Promise<{status: string; timestamp: string}> {
    return this.get('/health');
  }
  
  // Get API version
  async getVersion(): Promise<{version: string; build: string}> {
    return this.get('/version');
  }
}

// Export singleton instance
export const apiService = new ApiService();
