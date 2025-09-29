/**
 * Error Handler Utility
 * Centralized error handling for ArxOS Mobile
 */

import { logger } from './logger';

export enum ErrorType {
  NETWORK = 'NETWORK',
  AUTHENTICATION = 'AUTHENTICATION',
  VALIDATION = 'VALIDATION',
  STORAGE = 'STORAGE',
  CAMERA = 'CAMERA',
  LOCATION = 'LOCATION',
  AR = 'AR',
  SYNC = 'SYNC',
  UNKNOWN = 'UNKNOWN',
}

export enum ErrorSeverity {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL',
}

export interface AppError {
  type: ErrorType;
  severity: ErrorSeverity;
  message: string;
  code?: string;
  details?: any;
  timestamp: string;
  component?: string;
  stack?: string;
  retryable: boolean;
  userMessage?: string;
}

export class ArxOSError extends Error {
  public readonly type: ErrorType;
  public readonly severity: ErrorSeverity;
  public readonly code?: string;
  public readonly details?: any;
  public readonly component?: string;
  public readonly retryable: boolean;
  public readonly userMessage?: string;

  constructor(
    type: ErrorType,
    message: string,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    options: {
      code?: string;
      details?: any;
      component?: string;
      retryable?: boolean;
      userMessage?: string;
    } = {}
  ) {
    super(message);
    this.name = 'ArxOSError';
    this.type = type;
    this.severity = severity;
    this.code = options.code;
    this.details = options.details;
    this.component = options.component;
    this.retryable = options.retryable ?? false;
    this.userMessage = options.userMessage;
  }

  public toAppError(): AppError {
    return {
      type: this.type,
      severity: this.severity,
      message: this.message,
      code: this.code,
      details: this.details,
      timestamp: new Date().toISOString(),
      component: this.component,
      stack: this.stack,
      retryable: this.retryable,
      userMessage: this.userMessage,
    };
  }
}

class ErrorHandler {
  private errorHistory: AppError[] = [];
  private maxHistorySize = 100;

  public handleError(error: Error | ArxOSError, component?: string): AppError {
    let appError: AppError;

    if (error instanceof ArxOSError) {
      appError = error.toAppError();
    } else {
      appError = this.convertToAppError(error, component);
    }

    // Add to history
    this.addToHistory(appError);

    // Log the error
    this.logError(appError);

    // Handle based on severity
    this.handleBySeverity(appError);

    return appError;
  }

  private convertToAppError(error: Error, component?: string): AppError {
    const type = this.determineErrorType(error);
    const severity = this.determineErrorSeverity(error, type);
    const retryable = this.isRetryable(error, type);

    return {
      type,
      severity,
      message: error.message,
      timestamp: new Date().toISOString(),
      component,
      stack: error.stack,
      retryable,
      userMessage: this.getUserMessage(type, error.message),
    };
  }

  private determineErrorType(error: Error): ErrorType {
    const message = error.message.toLowerCase();

    if (message.includes('network') || message.includes('fetch') || message.includes('timeout')) {
      return ErrorType.NETWORK;
    }

    if (message.includes('auth') || message.includes('token') || message.includes('unauthorized')) {
      return ErrorType.AUTHENTICATION;
    }

    if (message.includes('validation') || message.includes('invalid') || message.includes('required')) {
      return ErrorType.VALIDATION;
    }

    if (message.includes('storage') || message.includes('database') || message.includes('sqlite')) {
      return ErrorType.STORAGE;
    }

    if (message.includes('camera') || message.includes('photo') || message.includes('image')) {
      return ErrorType.CAMERA;
    }

    if (message.includes('location') || message.includes('gps') || message.includes('geolocation')) {
      return ErrorType.LOCATION;
    }

    if (message.includes('ar') || message.includes('augmented') || message.includes('anchor')) {
      return ErrorType.AR;
    }

    if (message.includes('sync') || message.includes('synchronization')) {
      return ErrorType.SYNC;
    }

    return ErrorType.UNKNOWN;
  }

  private determineErrorSeverity(error: Error, type: ErrorType): ErrorSeverity {
    const message = error.message.toLowerCase();

    // Critical errors
    if (message.includes('fatal') || message.includes('critical') || type === ErrorType.AUTHENTICATION) {
      return ErrorSeverity.CRITICAL;
    }

    // High severity errors
    if (type === ErrorType.NETWORK || type === ErrorType.STORAGE) {
      return ErrorSeverity.HIGH;
    }

    // Medium severity errors
    if (type === ErrorType.VALIDATION || type === ErrorType.CAMERA || type === ErrorType.LOCATION) {
      return ErrorSeverity.MEDIUM;
    }

    // Low severity errors
    return ErrorSeverity.LOW;
  }

  private isRetryable(error: Error, type: ErrorType): boolean {
    const message = error.message.toLowerCase();

    // Network errors are usually retryable
    if (type === ErrorType.NETWORK) {
      return !message.includes('unauthorized') && !message.includes('forbidden');
    }

    // Storage errors might be retryable
    if (type === ErrorType.STORAGE) {
      return message.includes('locked') || message.includes('busy');
    }

    // Sync errors are usually retryable
    if (type === ErrorType.SYNC) {
      return true;
    }

    // Authentication errors are not retryable
    if (type === ErrorType.AUTHENTICATION) {
      return false;
    }

    return false;
  }

  private getUserMessage(type: ErrorType, message: string): string {
    switch (type) {
      case ErrorType.NETWORK:
        return 'Network connection error. Please check your internet connection and try again.';
      case ErrorType.AUTHENTICATION:
        return 'Authentication failed. Please log in again.';
      case ErrorType.VALIDATION:
        return 'Invalid input. Please check your data and try again.';
      case ErrorType.STORAGE:
        return 'Storage error. Please try again or contact support.';
      case ErrorType.CAMERA:
        return 'Camera error. Please check camera permissions and try again.';
      case ErrorType.LOCATION:
        return 'Location error. Please check location permissions and try again.';
      case ErrorType.AR:
        return 'AR error. Please try again or restart the app.';
      case ErrorType.SYNC:
        return 'Sync error. Data will be synchronized when connection is restored.';
      default:
        return 'An unexpected error occurred. Please try again.';
    }
  }

  private addToHistory(error: AppError): void {
    this.errorHistory.push(error);

    // Keep only the last maxHistorySize entries
    if (this.errorHistory.length > this.maxHistorySize) {
      this.errorHistory = this.errorHistory.slice(-this.maxHistorySize);
    }
  }

  private logError(error: AppError): void {
    const logData = {
      type: error.type,
      severity: error.severity,
      code: error.code,
      details: error.details,
      retryable: error.retryable,
    };

    switch (error.severity) {
      case ErrorSeverity.CRITICAL:
        logger.error(`Critical error: ${error.message}`, logData, error.component);
        break;
      case ErrorSeverity.HIGH:
        logger.error(`High severity error: ${error.message}`, logData, error.component);
        break;
      case ErrorSeverity.MEDIUM:
        logger.warn(`Medium severity error: ${error.message}`, logData, error.component);
        break;
      case ErrorSeverity.LOW:
        logger.info(`Low severity error: ${error.message}`, logData, error.component);
        break;
    }
  }

  private handleBySeverity(error: AppError): void {
    switch (error.severity) {
      case ErrorSeverity.CRITICAL:
        // Critical errors might require app restart or user intervention
        this.handleCriticalError(error);
        break;
      case ErrorSeverity.HIGH:
        // High severity errors might require user notification
        this.handleHighSeverityError(error);
        break;
      case ErrorSeverity.MEDIUM:
        // Medium severity errors might require retry logic
        this.handleMediumSeverityError(error);
        break;
      case ErrorSeverity.LOW:
        // Low severity errors can be logged and ignored
        break;
    }
  }

  private handleCriticalError(error: AppError): void {
    // Log critical error
    logger.error('Critical error occurred', error, 'ErrorHandler');
    
    // In a real app, you might want to:
    // - Show a critical error screen
    // - Force logout
    // - Restart the app
    // - Send crash report
  }

  private handleHighSeverityError(error: AppError): void {
    // Log high severity error
    logger.warn('High severity error occurred', error, 'ErrorHandler');
    
    // In a real app, you might want to:
    // - Show error notification
    // - Disable certain features
    // - Send error report
  }

  private handleMediumSeverityError(error: AppError): void {
    // Log medium severity error
    logger.info('Medium severity error occurred', error, 'ErrorHandler');
    
    // In a real app, you might want to:
    // - Implement retry logic
    // - Show warning message
  }

  public getErrorHistory(): AppError[] {
    return [...this.errorHistory];
  }

  public getErrorsByType(type: ErrorType): AppError[] {
    return this.errorHistory.filter(error => error.type === type);
  }

  public getErrorsBySeverity(severity: ErrorSeverity): AppError[] {
    return this.errorHistory.filter(error => error.severity === severity);
  }

  public clearErrorHistory(): void {
    this.errorHistory = [];
  }

  public exportErrorHistory(): string {
    return JSON.stringify(this.errorHistory, null, 2);
  }
}

// Create singleton instance
export const errorHandler = new ErrorHandler();

// Convenience functions
export const handleError = (error: Error | ArxOSError, component?: string) => 
  errorHandler.handleError(error, component);

export const createError = (
  type: ErrorType,
  message: string,
  severity: ErrorSeverity = ErrorSeverity.MEDIUM,
  options: {
    code?: string;
    details?: any;
    component?: string;
    retryable?: boolean;
    userMessage?: string;
  } = {}
) => new ArxOSError(type, message, severity, options);

export default errorHandler;
