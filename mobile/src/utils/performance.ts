/**
 * Performance Utilities
 * Tools for monitoring and optimizing app performance
 */

import {logger} from './logger';
import {errorHandler, ErrorType, ErrorSeverity, createError} from './errorHandler';

export interface PerformanceMetrics {
  memoryUsage: {
    used: number;
    total: number;
    free: number;
  };
  renderTime: number;
  networkLatency: number;
  batteryLevel?: number;
  timestamp: string;
}

export interface PerformanceThresholds {
  maxMemoryUsage: number; // MB
  maxRenderTime: number; // ms
  maxNetworkLatency: number; // ms
  minBatteryLevel: number; // percentage
}

class PerformanceMonitor {
  private metrics: PerformanceMetrics[] = [];
  private thresholds: PerformanceThresholds = {
    maxMemoryUsage: 100, // 100MB
    maxRenderTime: 100, // 100ms
    maxNetworkLatency: 5000, // 5 seconds
    minBatteryLevel: 20, // 20%
  };
  private isMonitoring = false;
  private monitoringInterval: NodeJS.Timeout | null = null;

  /**
   * Start performance monitoring
   */
  startMonitoring(intervalMs: number = 30000): void {
    if (this.isMonitoring) {
      logger.warn('Performance monitoring already started', {}, 'PerformanceMonitor');
      return;
    }

    logger.info('Starting performance monitoring', {intervalMs}, 'PerformanceMonitor');
    this.isMonitoring = true;

    this.monitoringInterval = setInterval(() => {
      this.collectMetrics();
    }, intervalMs);

    // Collect initial metrics
    this.collectMetrics();
  }

  /**
   * Stop performance monitoring
   */
  stopMonitoring(): void {
    if (!this.isMonitoring) {
      logger.warn('Performance monitoring not started', {}, 'PerformanceMonitor');
      return;
    }

    logger.info('Stopping performance monitoring', {}, 'PerformanceMonitor');
    this.isMonitoring = false;

    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = null;
    }
  }

  /**
   * Collect performance metrics
   */
  private async collectMetrics(): Promise<void> {
    try {
      const metrics: PerformanceMetrics = {
        memoryUsage: await this.getMemoryUsage(),
        renderTime: await this.getRenderTime(),
        networkLatency: await this.getNetworkLatency(),
        batteryLevel: await this.getBatteryLevel(),
        timestamp: new Date().toISOString(),
      };

      this.metrics.push(metrics);

      // Keep only last 100 metrics
      if (this.metrics.length > 100) {
        this.metrics = this.metrics.slice(-100);
      }

      // Check thresholds
      this.checkThresholds(metrics);

      logger.debug('Performance metrics collected', {metrics}, 'PerformanceMonitor');
    } catch (error) {
      logger.error('Failed to collect performance metrics', error, 'PerformanceMonitor');
    }
  }

  /**
   * Get memory usage
   */
  private async getMemoryUsage(): Promise<{used: number; total: number; free: number}> {
    try {
      // This would integrate with actual memory monitoring
      // For now, we'll return placeholder data
      return {
        used: 50, // MB
        total: 100, // MB
        free: 50, // MB
      };
    } catch (error) {
      logger.error('Failed to get memory usage', error, 'PerformanceMonitor');
      return {used: 0, total: 0, free: 0};
    }
  }

  /**
   * Get render time
   */
  private async getRenderTime(): Promise<number> {
    try {
      // This would measure actual render time
      // For now, we'll return placeholder data
      return 50; // ms
    } catch (error) {
      logger.error('Failed to get render time', error, 'PerformanceMonitor');
      return 0;
    }
  }

  /**
   * Get network latency
   */
  private async getNetworkLatency(): Promise<number> {
    try {
      // This would measure actual network latency
      // For now, we'll return placeholder data
      return 100; // ms
    } catch (error) {
      logger.error('Failed to get network latency', error, 'PerformanceMonitor');
      return 0;
    }
  }

  /**
   * Get battery level
   */
  private async getBatteryLevel(): Promise<number | undefined> {
    try {
      // This would integrate with battery monitoring
      // For now, we'll return placeholder data
      return 75; // percentage
    } catch (error) {
      logger.error('Failed to get battery level', error, 'PerformanceMonitor');
      return undefined;
    }
  }

  /**
   * Check performance thresholds
   */
  private checkThresholds(metrics: PerformanceMetrics): void {
    const warnings: string[] = [];

    if (metrics.memoryUsage.used > this.thresholds.maxMemoryUsage) {
      warnings.push(`High memory usage: ${metrics.memoryUsage.used}MB`);
    }

    if (metrics.renderTime > this.thresholds.maxRenderTime) {
      warnings.push(`Slow render time: ${metrics.renderTime}ms`);
    }

    if (metrics.networkLatency > this.thresholds.maxNetworkLatency) {
      warnings.push(`High network latency: ${metrics.networkLatency}ms`);
    }

    if (metrics.batteryLevel && metrics.batteryLevel < this.thresholds.minBatteryLevel) {
      warnings.push(`Low battery level: ${metrics.batteryLevel}%`);
    }

    if (warnings.length > 0) {
      logger.warn('Performance threshold exceeded', {warnings, metrics}, 'PerformanceMonitor');
      this.handlePerformanceWarning(warnings, metrics);
    }
  }

  /**
   * Handle performance warning
   */
  private handlePerformanceWarning(warnings: string[], metrics: PerformanceMetrics): void {
    // This could trigger various actions:
    // - Reduce image quality
    // - Disable animations
    // - Clear caches
    // - Show user notification
    
    logger.info('Handling performance warning', {warnings, metrics}, 'PerformanceMonitor');
  }

  /**
   * Get performance report
   */
  getPerformanceReport(): {
    current: PerformanceMetrics | null;
    average: Partial<PerformanceMetrics>;
    trends: {
      memoryTrend: 'up' | 'down' | 'stable';
      renderTrend: 'up' | 'down' | 'stable';
      networkTrend: 'up' | 'down' | 'stable';
    };
  } {
    const current = this.metrics[this.metrics.length - 1] || null;
    
    // Calculate averages
    const average = this.calculateAverages();
    
    // Calculate trends
    const trends = this.calculateTrends();

    return {
      current,
      average,
      trends,
    };
  }

  /**
   * Calculate average metrics
   */
  private calculateAverages(): Partial<PerformanceMetrics> {
    if (this.metrics.length === 0) {
      return {};
    }

    const sum = this.metrics.reduce(
      (acc, metric) => ({
        memoryUsage: {
          used: acc.memoryUsage.used + metric.memoryUsage.used,
          total: acc.memoryUsage.total + metric.memoryUsage.total,
          free: acc.memoryUsage.free + metric.memoryUsage.free,
        },
        renderTime: acc.renderTime + metric.renderTime,
        networkLatency: acc.networkLatency + metric.networkLatency,
        batteryLevel: (acc.batteryLevel || 0) + (metric.batteryLevel || 0),
      }),
      {
        memoryUsage: {used: 0, total: 0, free: 0},
        renderTime: 0,
        networkLatency: 0,
        batteryLevel: 0,
      }
    );

    const count = this.metrics.length;

    return {
      memoryUsage: {
        used: sum.memoryUsage.used / count,
        total: sum.memoryUsage.total / count,
        free: sum.memoryUsage.free / count,
      },
      renderTime: sum.renderTime / count,
      networkLatency: sum.networkLatency / count,
      batteryLevel: sum.batteryLevel / count,
    };
  }

  /**
   * Calculate trends
   */
  private calculateTrends(): {
    memoryTrend: 'up' | 'down' | 'stable';
    renderTrend: 'up' | 'down' | 'stable';
    networkTrend: 'up' | 'down' | 'stable';
  } {
    if (this.metrics.length < 2) {
      return {
        memoryTrend: 'stable',
        renderTrend: 'stable',
        networkTrend: 'stable',
      };
    }

    const recent = this.metrics.slice(-5); // Last 5 measurements
    const older = this.metrics.slice(-10, -5); // Previous 5 measurements

    const memoryTrend = this.calculateTrend(
      recent.map(m => m.memoryUsage.used),
      older.map(m => m.memoryUsage.used)
    );

    const renderTrend = this.calculateTrend(
      recent.map(m => m.renderTime),
      older.map(m => m.renderTime)
    );

    const networkTrend = this.calculateTrend(
      recent.map(m => m.networkLatency),
      older.map(m => m.networkLatency)
    );

    return {
      memoryTrend,
      renderTrend,
      networkTrend,
    };
  }

  /**
   * Calculate trend between two arrays
   */
  private calculateTrend(recent: number[], older: number[]): 'up' | 'down' | 'stable' {
    if (recent.length === 0 || older.length === 0) {
      return 'stable';
    }

    const recentAvg = recent.reduce((sum, val) => sum + val, 0) / recent.length;
    const olderAvg = older.reduce((sum, val) => sum + val, 0) / older.length;

    const diff = recentAvg - olderAvg;
    const threshold = olderAvg * 0.1; // 10% change threshold

    if (diff > threshold) {
      return 'up';
    } else if (diff < -threshold) {
      return 'down';
    } else {
      return 'stable';
    }
  }

  /**
   * Set performance thresholds
   */
  setThresholds(thresholds: Partial<PerformanceThresholds>): void {
    this.thresholds = {...this.thresholds, ...thresholds};
    logger.info('Performance thresholds updated', {thresholds: this.thresholds}, 'PerformanceMonitor');
  }

  /**
   * Clear metrics history
   */
  clearMetrics(): void {
    this.metrics = [];
    logger.info('Performance metrics cleared', {}, 'PerformanceMonitor');
  }

  /**
   * Get metrics history
   */
  getMetricsHistory(): PerformanceMetrics[] {
    return [...this.metrics];
  }
}

// Create singleton instance
export const performanceMonitor = new PerformanceMonitor();

// Utility functions for common performance optimizations
export const optimizeImages = (images: string[]): string[] => {
  // This would implement image optimization logic
  // For now, return original images
  return images;
};

export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean;
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
};

export const memoize = <T extends (...args: any[]) => any>(
  func: T,
  keyGenerator?: (...args: Parameters<T>) => string
): T => {
  const cache = new Map<string, ReturnType<T>>();
  
  return ((...args: Parameters<T>) => {
    const key = keyGenerator ? keyGenerator(...args) : JSON.stringify(args);
    
    if (cache.has(key)) {
      return cache.get(key);
    }
    
    const result = func(...args);
    cache.set(key, result);
    
    return result;
  }) as T;
};

export const lazyLoad = <T>(
  importFunction: () => Promise<T>
): Promise<T> => {
  return importFunction();
};

export default performanceMonitor;
