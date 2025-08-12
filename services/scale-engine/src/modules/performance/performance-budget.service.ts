import { Injectable, Logger } from '@nestjs/common';
import { EventEmitter2, OnEvent } from '@nestjs/event-emitter';
import { ConfigService } from '@nestjs/config';
import { PerformanceMonitorService } from '../metrics/performance-monitor.service';

export interface DeviceCapabilities {
  memory: number; // GB
  cores: number;
  gpu: 'low' | 'medium' | 'high' | 'discrete';
  connection: 'slow' | 'fast' | 'wifi' | 'cellular';
  screenSize: { width: number; height: number };
  pixelRatio: number;
}

export interface PerformanceBudget {
  // Rendering budget
  maxObjects: number;
  maxTriangles: number;
  maxTextures: number;
  maxTextureMemory: number; // MB
  
  // Network budget
  maxConcurrentRequests: number;
  maxBandwidthUsage: number; // MB/s
  maxLatency: number; // ms
  
  // CPU budget
  maxFrameTime: number; // ms
  maxProcessingTime: number; // ms per frame for non-rendering tasks
  
  // Memory budget
  maxTotalMemory: number; // MB
  maxCacheMemory: number; // MB
  
  // Quality settings
  levelOfDetail: number; // 1-5, higher = more detail
  shadowQuality: 'off' | 'low' | 'medium' | 'high';
  antiAliasing: 'off' | 'fxaa' | 'msaa2x' | 'msaa4x';
  textureQuality: 'low' | 'medium' | 'high';
}

export interface FrameMetrics {
  frameTime: number;
  drawCalls: number;
  triangles: number;
  objectsRendered: number;
  memoryUsed: number;
  gpuTime?: number;
}

export interface AdaptiveQualitySettings {
  objectCulling: number; // Distance culling factor
  lodBias: number; // Level of detail bias
  textureLod: number; // Texture mipmap bias
  shadowDistance: number;
  particleCount: number;
}

@Injectable()
export class PerformanceBudgetService {
  private readonly logger = new Logger(PerformanceBudgetService.name);
  
  // Current budget and capabilities
  private deviceCapabilities: DeviceCapabilities;
  private currentBudget: PerformanceBudget;
  private adaptiveSettings: AdaptiveQualitySettings;
  
  // Performance tracking
  private recentFrames: FrameMetrics[] = [];
  private readonly maxFrameHistory = 60; // Track last 60 frames
  
  // Budget enforcement
  private budgetViolations = 0;
  private consecutiveViolations = 0;
  private lastAdjustment = 0;
  
  // Quality adaptation
  private readonly qualityAdjustmentCooldown = 2000; // 2 seconds
  private targetFrameRate = 60;
  private currentFrameRate = 60;
  
  constructor(
    private readonly eventEmitter: EventEmitter2,
    private readonly configService: ConfigService,
    private readonly performanceMonitor: PerformanceMonitorService,
  ) {
    // Initialize with default capabilities
    this.deviceCapabilities = this.getDefaultCapabilities();
    this.currentBudget = this.calculateBudget(this.deviceCapabilities);
    this.adaptiveSettings = this.getDefaultAdaptiveSettings();
    
    this.targetFrameRate = this.configService.get('performance.targetFrameRate', 60);
  }

  /**
   * Initialize with detected device capabilities
   */
  initializeWithCapabilities(capabilities: Partial<DeviceCapabilities>): void {
    this.deviceCapabilities = {
      ...this.deviceCapabilities,
      ...capabilities,
    };
    
    this.currentBudget = this.calculateBudget(this.deviceCapabilities);
    this.adaptiveSettings = this.calculateAdaptiveSettings(this.deviceCapabilities);
    
    this.logger.log('Performance budget initialized', {
      capabilities: this.deviceCapabilities,
      budget: this.currentBudget,
    });
    
    this.eventEmitter.emit('performance.budget.initialized', {
      capabilities: this.deviceCapabilities,
      budget: this.currentBudget,
    });
  }

  /**
   * Calculate performance budget based on device capabilities
   */
  private calculateBudget(capabilities: DeviceCapabilities): PerformanceBudget {
    const baseBudget: PerformanceBudget = {
      maxObjects: 1000,
      maxTriangles: 50000,
      maxTextures: 50,
      maxTextureMemory: 100,
      maxConcurrentRequests: 6,
      maxBandwidthUsage: 1,
      maxLatency: 100,
      maxFrameTime: 16.67, // 60fps
      maxProcessingTime: 8,
      maxTotalMemory: 500,
      maxCacheMemory: 200,
      levelOfDetail: 3,
      shadowQuality: 'medium',
      antiAliasing: 'fxaa',
      textureQuality: 'medium',
    };
    
    // Adjust based on memory
    const memoryMultiplier = Math.min(capabilities.memory / 8, 2); // Scale based on 8GB baseline
    baseBudget.maxObjects = Math.floor(baseBudget.maxObjects * memoryMultiplier);
    baseBudget.maxTriangles = Math.floor(baseBudget.maxTriangles * memoryMultiplier);
    baseBudget.maxTotalMemory = Math.floor(baseBudget.maxTotalMemory * memoryMultiplier);
    baseBudget.maxCacheMemory = Math.floor(baseBudget.maxCacheMemory * memoryMultiplier);
    
    // Adjust based on CPU cores
    const coreMultiplier = Math.min(capabilities.cores / 4, 2); // Scale based on 4 cores baseline
    baseBudget.maxConcurrentRequests = Math.floor(baseBudget.maxConcurrentRequests * coreMultiplier);
    baseBudget.maxProcessingTime = Math.floor(baseBudget.maxProcessingTime * coreMultiplier);
    
    // Adjust based on GPU capability
    switch (capabilities.gpu) {
      case 'low':
        baseBudget.maxTriangles = Math.floor(baseBudget.maxTriangles * 0.5);
        baseBudget.maxTextures = Math.floor(baseBudget.maxTextures * 0.7);
        baseBudget.shadowQuality = 'off';
        baseBudget.antiAliasing = 'off';
        baseBudget.textureQuality = 'low';
        baseBudget.levelOfDetail = 2;
        break;
        
      case 'medium':
        baseBudget.maxTriangles = Math.floor(baseBudget.maxTriangles * 0.8);
        baseBudget.shadowQuality = 'low';
        baseBudget.antiAliasing = 'fxaa';
        baseBudget.textureQuality = 'medium';
        baseBudget.levelOfDetail = 3;
        break;
        
      case 'high':
        baseBudget.maxTriangles = Math.floor(baseBudget.maxTriangles * 1.2);
        baseBudget.shadowQuality = 'medium';
        baseBudget.antiAliasing = 'msaa2x';
        baseBudget.textureQuality = 'high';
        baseBudget.levelOfDetail = 4;
        break;
        
      case 'discrete':
        baseBudget.maxTriangles = Math.floor(baseBudget.maxTriangles * 1.5);
        baseBudget.maxTextures = Math.floor(baseBudget.maxTextures * 1.5);
        baseBudget.shadowQuality = 'high';
        baseBudget.antiAliasing = 'msaa4x';
        baseBudget.textureQuality = 'high';
        baseBudget.levelOfDetail = 5;
        break;
    }
    
    // Adjust based on connection speed
    switch (capabilities.connection) {
      case 'slow':
        baseBudget.maxConcurrentRequests = Math.floor(baseBudget.maxConcurrentRequests * 0.5);
        baseBudget.maxBandwidthUsage = 0.5;
        baseBudget.maxLatency = 500;
        break;
        
      case 'cellular':
        baseBudget.maxConcurrentRequests = Math.floor(baseBudget.maxConcurrentRequests * 0.7);
        baseBudget.maxBandwidthUsage = 0.8;
        baseBudget.maxLatency = 200;
        break;
        
      case 'wifi':
        baseBudget.maxConcurrentRequests = Math.floor(baseBudget.maxConcurrentRequests * 1.2);
        baseBudget.maxBandwidthUsage = 2;
        baseBudget.maxLatency = 50;
        break;
        
      case 'fast':
        baseBudget.maxConcurrentRequests = Math.floor(baseBudget.maxConcurrentRequests * 1.5);
        baseBudget.maxBandwidthUsage = 5;
        baseBudget.maxLatency = 20;
        break;
    }
    
    // Adjust based on screen size (higher resolution = more demanding)
    const screenArea = capabilities.screenSize.width * capabilities.screenSize.height;
    const baselineArea = 1920 * 1080;
    const resolutionMultiplier = Math.sqrt(screenArea / baselineArea);
    
    baseBudget.maxTriangles = Math.floor(baseBudget.maxTriangles / resolutionMultiplier);
    baseBudget.maxTextureMemory = Math.floor(baseBudget.maxTextureMemory * resolutionMultiplier);
    
    return baseBudget;
  }

  /**
   * Calculate adaptive quality settings
   */
  private calculateAdaptiveSettings(capabilities: DeviceCapabilities): AdaptiveQualitySettings {
    const baseSettings: AdaptiveQualitySettings = {
      objectCulling: 1.0,
      lodBias: 0.0,
      textureLod: 0.0,
      shadowDistance: 100.0,
      particleCount: 1.0,
    };
    
    // Adjust based on GPU capability
    switch (capabilities.gpu) {
      case 'low':
        baseSettings.objectCulling = 0.7;
        baseSettings.lodBias = 1.0;
        baseSettings.textureLod = 1.0;
        baseSettings.shadowDistance = 30.0;
        baseSettings.particleCount = 0.3;
        break;
        
      case 'medium':
        baseSettings.objectCulling = 0.85;
        baseSettings.lodBias = 0.5;
        baseSettings.textureLod = 0.5;
        baseSettings.shadowDistance = 70.0;
        baseSettings.particleCount = 0.7;
        break;
        
      case 'high':
        baseSettings.objectCulling = 1.0;
        baseSettings.lodBias = 0.0;
        baseSettings.textureLod = 0.0;
        baseSettings.shadowDistance = 150.0;
        baseSettings.particleCount = 1.0;
        break;
        
      case 'discrete':
        baseSettings.objectCulling = 1.2;
        baseSettings.lodBias = -0.5;
        baseSettings.textureLod = -0.5;
        baseSettings.shadowDistance = 200.0;
        baseSettings.particleCount = 1.5;
        break;
    }
    
    return baseSettings;
  }

  /**
   * Track frame performance and adjust budget
   */
  @OnEvent('render.frame.complete')
  trackFramePerformance(metrics: FrameMetrics): void {
    this.recentFrames.push(metrics);
    
    // Limit frame history
    if (this.recentFrames.length > this.maxFrameHistory) {
      this.recentFrames.shift();
    }
    
    // Update current frame rate
    this.updateFrameRate();
    
    // Check for budget violations
    this.checkBudgetViolations(metrics);
    
    // Adapt quality if needed
    this.adaptQualitySettings();
  }

  /**
   * Update current frame rate estimate
   */
  private updateFrameRate(): void {
    if (this.recentFrames.length < 10) return;
    
    const recentAverage = this.recentFrames
      .slice(-10)
      .reduce((sum, frame) => sum + frame.frameTime, 0) / 10;
    
    this.currentFrameRate = Math.min(1000 / recentAverage, 60);
  }

  /**
   * Check for budget violations
   */
  private checkBudgetViolations(metrics: FrameMetrics): void {
    let violations = 0;
    
    if (metrics.frameTime > this.currentBudget.maxFrameTime) violations++;
    if (metrics.objectsRendered > this.currentBudget.maxObjects) violations++;
    if (metrics.triangles > this.currentBudget.maxTriangles) violations++;
    if (metrics.memoryUsed > this.currentBudget.maxTotalMemory) violations++;
    
    if (violations > 0) {
      this.budgetViolations++;
      this.consecutiveViolations++;
      
      this.logger.warn(`Performance budget violations: ${violations}`, {
        frameTime: metrics.frameTime,
        maxFrameTime: this.currentBudget.maxFrameTime,
        objects: metrics.objectsRendered,
        maxObjects: this.currentBudget.maxObjects,
      });
    } else {
      this.consecutiveViolations = 0;
    }
  }

  /**
   * Adapt quality settings based on performance
   */
  private adaptQualitySettings(): void {
    const now = Date.now();
    
    // Cooldown check
    if (now - this.lastAdjustment < this.qualityAdjustmentCooldown) {
      return;
    }
    
    const targetFps = this.targetFrameRate;
    const currentFps = this.currentFrameRate;
    const fpsRatio = currentFps / targetFps;
    
    // Determine if we need to adjust quality
    let shouldDecrease = false;
    let shouldIncrease = false;
    
    if (fpsRatio < 0.9 || this.consecutiveViolations > 5) {
      shouldDecrease = true;
    } else if (fpsRatio > 1.05 && this.consecutiveViolations === 0) {
      shouldIncrease = true;
    }
    
    if (shouldDecrease) {
      this.decreaseQuality();
      this.lastAdjustment = now;
    } else if (shouldIncrease) {
      this.increaseQuality();
      this.lastAdjustment = now;
    }
  }

  /**
   * Decrease quality to improve performance
   */
  private decreaseQuality(): void {
    // Reduce level of detail
    if (this.currentBudget.levelOfDetail > 1) {
      this.currentBudget.levelOfDetail--;
    }
    
    // Reduce object count
    this.currentBudget.maxObjects = Math.floor(this.currentBudget.maxObjects * 0.8);
    
    // Reduce triangle count
    this.currentBudget.maxTriangles = Math.floor(this.currentBudget.maxTriangles * 0.8);
    
    // Adjust adaptive settings
    this.adaptiveSettings.objectCulling = Math.max(0.5, this.adaptiveSettings.objectCulling * 0.9);
    this.adaptiveSettings.lodBias = Math.min(2.0, this.adaptiveSettings.lodBias + 0.2);
    this.adaptiveSettings.particleCount = Math.max(0.1, this.adaptiveSettings.particleCount * 0.8);
    
    // Downgrade quality settings
    if (this.currentBudget.antiAliasing === 'msaa4x') {
      this.currentBudget.antiAliasing = 'msaa2x';
    } else if (this.currentBudget.antiAliasing === 'msaa2x') {
      this.currentBudget.antiAliasing = 'fxaa';
    } else if (this.currentBudget.antiAliasing === 'fxaa') {
      this.currentBudget.antiAliasing = 'off';
    }
    
    if (this.currentBudget.shadowQuality === 'high') {
      this.currentBudget.shadowQuality = 'medium';
    } else if (this.currentBudget.shadowQuality === 'medium') {
      this.currentBudget.shadowQuality = 'low';
    } else if (this.currentBudget.shadowQuality === 'low') {
      this.currentBudget.shadowQuality = 'off';
    }
    
    this.logger.log('Quality decreased to improve performance', {
      levelOfDetail: this.currentBudget.levelOfDetail,
      maxObjects: this.currentBudget.maxObjects,
      antiAliasing: this.currentBudget.antiAliasing,
      shadowQuality: this.currentBudget.shadowQuality,
    });
    
    this.eventEmitter.emit('performance.quality.decreased', {
      budget: this.currentBudget,
      adaptiveSettings: this.adaptiveSettings,
    });
  }

  /**
   * Increase quality if performance allows
   */
  private increaseQuality(): void {
    // Only increase if we're not at maximum already
    const originalBudget = this.calculateBudget(this.deviceCapabilities);
    
    if (this.currentBudget.levelOfDetail < originalBudget.levelOfDetail) {
      this.currentBudget.levelOfDetail++;
    }
    
    if (this.currentBudget.maxObjects < originalBudget.maxObjects) {
      this.currentBudget.maxObjects = Math.min(
        originalBudget.maxObjects,
        Math.floor(this.currentBudget.maxObjects * 1.1),
      );
    }
    
    if (this.currentBudget.maxTriangles < originalBudget.maxTriangles) {
      this.currentBudget.maxTriangles = Math.min(
        originalBudget.maxTriangles,
        Math.floor(this.currentBudget.maxTriangles * 1.1),
      );
    }
    
    // Improve adaptive settings
    this.adaptiveSettings.objectCulling = Math.min(1.2, this.adaptiveSettings.objectCulling * 1.05);
    this.adaptiveSettings.lodBias = Math.max(-0.5, this.adaptiveSettings.lodBias - 0.1);
    this.adaptiveSettings.particleCount = Math.min(1.5, this.adaptiveSettings.particleCount * 1.1);
    
    this.logger.debug('Quality increased', {
      levelOfDetail: this.currentBudget.levelOfDetail,
      maxObjects: this.currentBudget.maxObjects,
    });
    
    this.eventEmitter.emit('performance.quality.increased', {
      budget: this.currentBudget,
      adaptiveSettings: this.adaptiveSettings,
    });
  }

  /**
   * Get default device capabilities
   */
  private getDefaultCapabilities(): DeviceCapabilities {
    return {
      memory: 8, // GB
      cores: 4,
      gpu: 'medium',
      connection: 'wifi',
      screenSize: { width: 1920, height: 1080 },
      pixelRatio: 1,
    };
  }

  /**
   * Get default adaptive settings
   */
  private getDefaultAdaptiveSettings(): AdaptiveQualitySettings {
    return {
      objectCulling: 1.0,
      lodBias: 0.0,
      textureLod: 0.0,
      shadowDistance: 100.0,
      particleCount: 1.0,
    };
  }

  /**
   * Get current performance budget
   */
  getCurrentBudget(): PerformanceBudget {
    return { ...this.currentBudget };
  }

  /**
   * Get current adaptive settings
   */
  getAdaptiveSettings(): AdaptiveQualitySettings {
    return { ...this.adaptiveSettings };
  }

  /**
   * Get device capabilities
   */
  getDeviceCapabilities(): DeviceCapabilities {
    return { ...this.deviceCapabilities };
  }

  /**
   * Get performance statistics
   */
  getPerformanceStats(): any {
    if (this.recentFrames.length === 0) {
      return {
        currentFrameRate: 0,
        averageFrameTime: 0,
        budgetViolations: this.budgetViolations,
        consecutiveViolations: this.consecutiveViolations,
      };
    }
    
    const averageFrameTime = this.recentFrames
      .reduce((sum, frame) => sum + frame.frameTime, 0) / this.recentFrames.length;
    
    const averageObjects = this.recentFrames
      .reduce((sum, frame) => sum + frame.objectsRendered, 0) / this.recentFrames.length;
    
    const averageTriangles = this.recentFrames
      .reduce((sum, frame) => sum + frame.triangles, 0) / this.recentFrames.length;
    
    return {
      currentFrameRate: this.currentFrameRate.toFixed(1),
      averageFrameTime: averageFrameTime.toFixed(2),
      averageObjects: Math.round(averageObjects),
      averageTriangles: Math.round(averageTriangles),
      budgetViolations: this.budgetViolations,
      consecutiveViolations: this.consecutiveViolations,
      frameHistorySize: this.recentFrames.length,
    };
  }

  /**
   * Reset statistics
   */
  resetStatistics(): void {
    this.recentFrames = [];
    this.budgetViolations = 0;
    this.consecutiveViolations = 0;
    this.lastAdjustment = 0;
    this.logger.log('Performance statistics reset');
  }

  /**
   * Override budget for testing or manual control
   */
  setBudgetOverride(budget: Partial<PerformanceBudget>): void {
    this.currentBudget = {
      ...this.currentBudget,
      ...budget,
    };
    
    this.eventEmitter.emit('performance.budget.overridden', {
      budget: this.currentBudget,
    });
    
    this.logger.log('Performance budget overridden', budget);
  }
}