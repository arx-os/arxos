/**
 * Logger Utility
 * Centralized logging system for ArxOS Mobile
 */

import { environment } from '../config/environment';

export enum LogLevel {
  ERROR = 0,
  WARN = 1,
  INFO = 2,
  DEBUG = 3,
}

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  data?: any;
  stack?: string;
  component?: string;
}

class Logger {
  private logLevel: LogLevel;
  private logs: LogEntry[] = [];
  private maxLogs = 1000;

  constructor() {
    this.logLevel = this.getLogLevelFromString(environment.logLevel);
  }

  private getLogLevelFromString(level: string): LogLevel {
    switch (level.toLowerCase()) {
      case 'error':
        return LogLevel.ERROR;
      case 'warn':
        return LogLevel.WARN;
      case 'info':
        return LogLevel.INFO;
      case 'debug':
        return LogLevel.DEBUG;
      default:
        return LogLevel.INFO;
    }
  }

  private shouldLog(level: LogLevel): boolean {
    return level <= this.logLevel;
  }

  private formatMessage(level: LogLevel, message: string, data?: any, component?: string): string {
    const timestamp = new Date().toISOString();
    const levelName = LogLevel[level];
    const componentStr = component ? `[${component}] ` : '';
    
    if (data) {
      return `${timestamp} ${levelName} ${componentStr}${message} ${JSON.stringify(data)}`;
    }
    
    return `${timestamp} ${levelName} ${componentStr}${message}`;
  }

  private addLog(level: LogLevel, message: string, data?: any, component?: string, stack?: string): void {
    if (!this.shouldLog(level)) {
      return;
    }

    const logEntry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      data,
      stack,
      component,
    };

    this.logs.push(logEntry);

    // Keep only the last maxLogs entries
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(-this.maxLogs);
    }

    // Console output
    const formattedMessage = this.formatMessage(level, message, data, component);
    
    switch (level) {
      case LogLevel.ERROR:
        console.error(formattedMessage);
        if (stack) {
          console.error(stack);
        }
        break;
      case LogLevel.WARN:
        console.warn(formattedMessage);
        break;
      case LogLevel.INFO:
        console.info(formattedMessage);
        break;
      case LogLevel.DEBUG:
        if (environment.debugMode) {
          console.log(formattedMessage);
        }
        break;
    }
  }

  public error(message: string, data?: any, component?: string): void {
    const stack = new Error().stack;
    this.addLog(LogLevel.ERROR, message, data, component, stack);
  }

  public warn(message: string, data?: any, component?: string): void {
    this.addLog(LogLevel.WARN, message, data, component);
  }

  public info(message: string, data?: any, component?: string): void {
    this.addLog(LogLevel.INFO, message, data, component);
  }

  public debug(message: string, data?: any, component?: string): void {
    this.addLog(LogLevel.DEBUG, message, data, component);
  }

  public getLogs(): LogEntry[] {
    return [...this.logs];
  }

  public getLogsByLevel(level: LogLevel): LogEntry[] {
    return this.logs.filter(log => log.level === level);
  }

  public getLogsByComponent(component: string): LogEntry[] {
    return this.logs.filter(log => log.component === component);
  }

  public clearLogs(): void {
    this.logs = [];
  }

  public exportLogs(): string {
    return JSON.stringify(this.logs, null, 2);
  }

  public setLogLevel(level: LogLevel): void {
    this.logLevel = level;
  }

  public setLogLevelFromString(level: string): void {
    this.logLevel = this.getLogLevelFromString(level);
  }
}

// Create singleton instance
export const logger = new Logger();

// Convenience functions
export const logError = (message: string, data?: any, component?: string) => 
  logger.error(message, data, component);

export const logWarn = (message: string, data?: any, component?: string) => 
  logger.warn(message, data, component);

export const logInfo = (message: string, data?: any, component?: string) => 
  logger.info(message, data, component);

export const logDebug = (message: string, data?: any, component?: string) => 
  logger.debug(message, data, component);

export default logger;
