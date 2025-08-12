import { Injectable, Logger } from '@nestjs/common';
import { EventEmitter2, OnEvent } from '@nestjs/event-emitter';
import { ConfigService } from '@nestjs/config';
import * as tf from '@tensorflow/tfjs-node';

import { AdvancedTileLoaderService, TileCoordinate, TileRequest } from './advanced-tile-loader.service';
import { PerformanceMonitorService } from '../metrics/performance-monitor.service';

export interface UserBehavior {
  timestamp: Date;
  action: 'zoom' | 'pan' | 'idle';
  fromScale?: number;
  toScale?: number;
  fromCenter?: { x: number; y: number };
  toCenter?: { x: number; y: number };
  velocity?: { x: number; y: number };
  duration?: number;
}

export interface PredictionResult {
  tiles: TileCoordinate[];
  confidence: number;
  predictedAction: 'zoom-in' | 'zoom-out' | 'pan' | 'explore';
  priority: 'high' | 'normal' | 'low';
}

export interface MovementPattern {
  direction: 'north' | 'south' | 'east' | 'west' | 'northeast' | 'northwest' | 'southeast' | 'southwest';
  speed: 'slow' | 'medium' | 'fast';
  consistency: number; // 0-1, how consistent the movement is
}

@Injectable()
export class PredictivePreloaderService {
  private readonly logger = new Logger(PredictivePreloaderService.name);
  
  // User behavior tracking
  private readonly behaviorHistory: Map<string, UserBehavior[]> = new Map();
  private readonly maxHistorySize = 100;
  
  // Movement prediction
  private movementModel: tf.LayersModel | null = null;
  private readonly movementPatterns: Map<string, MovementPattern[]> = new Map();
  
  // Preloading configuration
  private readonly preloadRadius: number;
  private readonly preloadLevels: number;
  private readonly confidenceThreshold: number;
  
  // Statistics
  private preloadHits = 0;
  private preloadMisses = 0;
  private totalPreloaded = 0;
  
  constructor(
    private readonly tileLoader: AdvancedTileLoaderService,
    private readonly eventEmitter: EventEmitter2,
    private readonly configService: ConfigService,
    private readonly performanceMonitor: PerformanceMonitorService,
  ) {
    this.preloadRadius = this.configService.get('preload.radius', 3);
    this.preloadLevels = this.configService.get('preload.levels', 2);
    this.confidenceThreshold = this.configService.get('preload.confidenceThreshold', 0.6);
    
    // Initialize movement prediction model
    this.initializeModel();
  }

  /**
   * Initialize TensorFlow.js model for movement prediction
   */
  private async initializeModel(): Promise<void> {
    try {
      // Create a simple LSTM model for movement prediction
      const model = tf.sequential({
        layers: [
          tf.layers.lstm({
            units: 32,
            returnSequences: true,
            inputShape: [10, 6], // 10 time steps, 6 features
          }),
          tf.layers.lstm({
            units: 16,
            returnSequences: false,
          }),
          tf.layers.dense({
            units: 8,
            activation: 'relu',
          }),
          tf.layers.dense({
            units: 4,
            activation: 'softmax', // 4 actions: zoom-in, zoom-out, pan, explore
          }),
        ],
      });
      
      model.compile({
        optimizer: 'adam',
        loss: 'categoricalCrossentropy',
        metrics: ['accuracy'],
      });
      
      this.movementModel = model;
      this.logger.log('Movement prediction model initialized');
    } catch (error) {
      this.logger.error('Failed to initialize movement model:', error);
    }
  }

  /**
   * Track user behavior for prediction
   */
  @OnEvent('viewport.*')
  trackUserBehavior(event: any): void {
    const userId = event.userId || 'default';
    
    const behavior: UserBehavior = {
      timestamp: new Date(),
      action: this.getActionFromEvent(event.type),
      fromScale: event.fromScale,
      toScale: event.toScale || event.scale,
      fromCenter: event.fromCenter,
      toCenter: event.toCenter || event.center,
      velocity: event.velocity,
      duration: event.duration,
    };
    
    // Store behavior
    if (!this.behaviorHistory.has(userId)) {
      this.behaviorHistory.set(userId, []);
    }
    
    const history = this.behaviorHistory.get(userId)!;
    history.push(behavior);
    
    // Limit history size
    if (history.length > this.maxHistorySize) {
      history.shift();
    }
    
    // Trigger prediction
    this.predictAndPreload(userId, behavior);
  }

  /**
   * Predict user's next action and preload accordingly
   */
  private async predictAndPreload(userId: string, currentBehavior: UserBehavior): Promise<void> {
    const history = this.behaviorHistory.get(userId);
    if (!history || history.length < 5) {
      // Not enough history for prediction
      return;
    }
    
    const prediction = await this.predictNextAction(history);
    
    if (prediction.confidence < this.confidenceThreshold) {
      this.logger.debug(`Low confidence prediction (${prediction.confidence}), skipping preload`);
      return;
    }
    
    // Preload based on prediction
    await this.executePreload(prediction, currentBehavior);
  }

  /**
   * Predict next user action using ML model
   */
  private async predictNextAction(history: UserBehavior[]): Promise<PredictionResult> {
    // Analyze recent movement patterns
    const pattern = this.analyzeMovementPattern(history.slice(-10));
    
    // Use ML model if available
    if (this.movementModel) {
      try {
        const features = this.extractFeatures(history.slice(-10));
        const input = tf.tensor3d([features]);
        const prediction = this.movementModel.predict(input) as tf.Tensor;
        const probabilities = await prediction.array() as number[][];
        
        input.dispose();
        prediction.dispose();
        
        const actions = ['zoom-in', 'zoom-out', 'pan', 'explore'] as const;
        const maxIndex = probabilities[0].indexOf(Math.max(...probabilities[0]));
        const predictedAction = actions[maxIndex];
        const confidence = probabilities[0][maxIndex];
        
        return {
          tiles: this.calculateTilesToPreload(pattern, predictedAction),
          confidence,
          predictedAction,
          priority: confidence > 0.8 ? 'high' : confidence > 0.6 ? 'normal' : 'low',
        };
      } catch (error) {
        this.logger.error('ML prediction failed:', error);
      }
    }
    
    // Fallback to heuristic prediction
    return this.heuristicPrediction(pattern);
  }

  /**
   * Heuristic-based prediction fallback
   */
  private heuristicPrediction(pattern: MovementPattern): PredictionResult {
    let predictedAction: PredictionResult['predictedAction'] = 'explore';
    let confidence = 0.5;
    
    // Determine action based on pattern
    if (pattern.consistency > 0.7) {
      predictedAction = 'pan';
      confidence = pattern.consistency;
    } else if (pattern.speed === 'fast') {
      predictedAction = 'zoom-out';
      confidence = 0.6;
    } else if (pattern.speed === 'slow') {
      predictedAction = 'zoom-in';
      confidence = 0.6;
    }
    
    return {
      tiles: this.calculateTilesToPreload(pattern, predictedAction),
      confidence,
      predictedAction,
      priority: confidence > 0.7 ? 'normal' : 'low',
    };
  }

  /**
   * Calculate which tiles to preload based on prediction
   */
  private calculateTilesToPreload(
    pattern: MovementPattern,
    action: PredictionResult['predictedAction'],
  ): TileCoordinate[] {
    const tiles: TileCoordinate[] = [];
    
    switch (action) {
      case 'zoom-in':
        // Preload higher resolution tiles for center area
        tiles.push(...this.getZoomInTiles(pattern));
        break;
        
      case 'zoom-out':
        // Preload lower resolution surrounding tiles
        tiles.push(...this.getZoomOutTiles(pattern));
        break;
        
      case 'pan':
        // Preload tiles in movement direction
        tiles.push(...this.getPanTiles(pattern));
        break;
        
      case 'explore':
        // Preload adjacent tiles in all directions
        tiles.push(...this.getExploreTiles());
        break;
    }
    
    return tiles;
  }

  /**
   * Get tiles for zoom-in prediction
   */
  private getZoomInTiles(pattern: MovementPattern): TileCoordinate[] {
    const tiles: TileCoordinate[] = [];
    const centerZ = 15; // Example zoom level
    
    // Preload center tiles at higher zoom
    for (let z = centerZ + 1; z <= Math.min(centerZ + this.preloadLevels, 22); z++) {
      const scale = Math.pow(2, z - centerZ);
      for (let dx = -1; dx <= 1; dx++) {
        for (let dy = -1; dy <= 1; dy++) {
          tiles.push({
            z,
            x: Math.floor(512 * scale) + dx,
            y: Math.floor(512 * scale) + dy,
          });
        }
      }
    }
    
    return tiles;
  }

  /**
   * Get tiles for zoom-out prediction
   */
  private getZoomOutTiles(pattern: MovementPattern): TileCoordinate[] {
    const tiles: TileCoordinate[] = [];
    const centerZ = 15; // Example zoom level
    
    // Preload surrounding tiles at lower zoom
    for (let z = Math.max(centerZ - this.preloadLevels, 0); z < centerZ; z++) {
      const scale = Math.pow(2, centerZ - z);
      for (let dx = -this.preloadRadius; dx <= this.preloadRadius; dx++) {
        for (let dy = -this.preloadRadius; dy <= this.preloadRadius; dy++) {
          tiles.push({
            z,
            x: Math.floor(512 / scale) + dx,
            y: Math.floor(512 / scale) + dy,
          });
        }
      }
    }
    
    return tiles;
  }

  /**
   * Get tiles for pan prediction
   */
  private getPanTiles(pattern: MovementPattern): TileCoordinate[] {
    const tiles: TileCoordinate[] = [];
    const z = 15; // Current zoom level
    
    // Calculate offset based on direction
    const offsets = this.getDirectionOffsets(pattern.direction);
    
    // Preload tiles in movement direction
    for (let distance = 1; distance <= this.preloadRadius; distance++) {
      const x = 512 + offsets.x * distance;
      const y = 512 + offsets.y * distance;
      
      // Add tiles in a cone shape
      for (let spread = -1; spread <= 1; spread++) {
        tiles.push({
          z,
          x: x + spread * offsets.y, // Perpendicular spread
          y: y + spread * offsets.x,
        });
      }
    }
    
    return tiles;
  }

  /**
   * Get tiles for exploration
   */
  private getExploreTiles(): TileCoordinate[] {
    const tiles: TileCoordinate[] = [];
    const z = 15; // Current zoom level
    
    // Preload all adjacent tiles
    for (let dx = -this.preloadRadius; dx <= this.preloadRadius; dx++) {
      for (let dy = -this.preloadRadius; dy <= this.preloadRadius; dy++) {
        if (dx === 0 && dy === 0) continue; // Skip center
        
        const distance = Math.sqrt(dx * dx + dy * dy);
        if (distance <= this.preloadRadius) {
          tiles.push({
            z,
            x: 512 + dx,
            y: 512 + dy,
          });
        }
      }
    }
    
    return tiles;
  }

  /**
   * Execute preloading of predicted tiles
   */
  private async executePreload(
    prediction: PredictionResult,
    currentBehavior: UserBehavior,
  ): Promise<void> {
    const scale = currentBehavior.toScale || 1.0;
    
    this.logger.debug(
      `Preloading ${prediction.tiles.length} tiles for predicted ${prediction.predictedAction} ` +
      `(confidence: ${prediction.confidence.toFixed(2)})`,
    );
    
    // Queue tiles for preloading
    const requests: TileRequest[] = prediction.tiles.map(coordinate => ({
      coordinate,
      scale,
      priority: prediction.priority,
    }));
    
    // Load tiles asynchronously
    const startTime = Date.now();
    const promises = requests.map(req => this.tileLoader.loadTile(req));
    
    Promise.all(promises).then(tiles => {
      const duration = Date.now() - startTime;
      this.totalPreloaded += tiles.length;
      
      this.eventEmitter.emit('preload.completed', {
        predictedAction: prediction.predictedAction,
        tilesLoaded: tiles.length,
        confidence: prediction.confidence,
        duration,
      });
      
      this.logger.debug(`Preloaded ${tiles.length} tiles in ${duration}ms`);
    }).catch(error => {
      this.logger.error('Preloading failed:', error);
    });
  }

  /**
   * Analyze movement pattern from behavior history
   */
  private analyzeMovementPattern(history: UserBehavior[]): MovementPattern {
    if (history.length < 2) {
      return {
        direction: 'north',
        speed: 'medium',
        consistency: 0,
      };
    }
    
    // Calculate average direction
    let totalDx = 0;
    let totalDy = 0;
    let consistentMoves = 0;
    
    for (let i = 1; i < history.length; i++) {
      const prev = history[i - 1];
      const curr = history[i];
      
      if (prev.toCenter && curr.fromCenter) {
        const dx = curr.fromCenter.x - prev.toCenter.x;
        const dy = curr.fromCenter.y - prev.toCenter.y;
        
        totalDx += dx;
        totalDy += dy;
        
        if (Math.abs(dx) > 0 || Math.abs(dy) > 0) {
          consistentMoves++;
        }
      }
    }
    
    const avgDx = totalDx / history.length;
    const avgDy = totalDy / history.length;
    
    // Determine direction
    const direction = this.getDirection(avgDx, avgDy);
    
    // Determine speed
    const avgVelocity = Math.sqrt(avgDx * avgDx + avgDy * avgDy);
    const speed = avgVelocity > 100 ? 'fast' : avgVelocity > 50 ? 'medium' : 'slow';
    
    // Calculate consistency
    const consistency = consistentMoves / (history.length - 1);
    
    return { direction, speed, consistency };
  }

  /**
   * Extract features for ML model
   */
  private extractFeatures(history: UserBehavior[]): number[][] {
    return history.map(behavior => {
      const action = behavior.action === 'zoom' ? 1 : behavior.action === 'pan' ? 2 : 0;
      const scale = behavior.toScale || 1;
      const centerX = behavior.toCenter?.x || 0;
      const centerY = behavior.toCenter?.y || 0;
      const velocityX = behavior.velocity?.x || 0;
      const velocityY = behavior.velocity?.y || 0;
      
      return [action, scale, centerX, centerY, velocityX, velocityY];
    });
  }

  /**
   * Get direction from dx, dy
   */
  private getDirection(dx: number, dy: number): MovementPattern['direction'] {
    const angle = Math.atan2(dy, dx) * 180 / Math.PI;
    
    if (angle >= -22.5 && angle < 22.5) return 'east';
    if (angle >= 22.5 && angle < 67.5) return 'northeast';
    if (angle >= 67.5 && angle < 112.5) return 'north';
    if (angle >= 112.5 && angle < 157.5) return 'northwest';
    if (angle >= 157.5 || angle < -157.5) return 'west';
    if (angle >= -157.5 && angle < -112.5) return 'southwest';
    if (angle >= -112.5 && angle < -67.5) return 'south';
    return 'southeast';
  }

  /**
   * Get direction offsets for preloading
   */
  private getDirectionOffsets(direction: MovementPattern['direction']): { x: number; y: number } {
    switch (direction) {
      case 'north': return { x: 0, y: -1 };
      case 'south': return { x: 0, y: 1 };
      case 'east': return { x: 1, y: 0 };
      case 'west': return { x: -1, y: 0 };
      case 'northeast': return { x: 1, y: -1 };
      case 'northwest': return { x: -1, y: -1 };
      case 'southeast': return { x: 1, y: 1 };
      case 'southwest': return { x: -1, y: 1 };
    }
  }

  /**
   * Get action type from event
   */
  private getActionFromEvent(eventType: string): UserBehavior['action'] {
    if (eventType.includes('zoom')) return 'zoom';
    if (eventType.includes('pan')) return 'pan';
    return 'idle';
  }

  /**
   * Get preloading statistics
   */
  getStatistics(): any {
    const hitRate = this.preloadHits / (this.preloadHits + this.preloadMisses) || 0;
    
    return {
      totalPreloaded: this.totalPreloaded,
      hitRate: hitRate.toFixed(2),
      hits: this.preloadHits,
      misses: this.preloadMisses,
      behaviorHistorySize: this.behaviorHistory.size,
      modelLoaded: this.movementModel !== null,
    };
  }

  /**
   * Update hit/miss statistics
   */
  @OnEvent('tile.requested')
  updateStatistics(event: any): void {
    const tileKey = `${event.z}:${event.x}:${event.y}`;
    
    // Check if this tile was preloaded
    // This would need to track preloaded tiles
    // For now, simplified implementation
    
    // Update statistics based on whether tile was in cache
    if (event.source === 'memory' || event.source === 'redis') {
      this.preloadHits++;
    } else {
      this.preloadMisses++;
    }
  }
}