import { Injectable, Logger } from '@nestjs/common';
import { EventEmitter2 } from '@nestjs/event-emitter';
import { register, Counter, Histogram, Gauge } from 'prom-client';

@Injectable()
export class PerformanceMonitorService {
  private readonly logger = new Logger(PerformanceMonitorService.name);
  
  // Metrics
  private readonly zoomDuration: Histogram<string>;
  private readonly queryDuration: Histogram<string>;
  private readonly cacheHits: Counter<string>;
  private readonly cacheMisses: Counter<string>;
  private readonly activeViewports: Gauge<string>;
  private readonly visibleObjects: Gauge<string>;

  constructor(private readonly eventEmitter: EventEmitter2) {
    // Initialize metrics
    this.zoomDuration = new Histogram({
      name: 'fractal_zoom_duration_ms',
      help: 'Zoom transition duration in milliseconds',
      labelNames: ['from_scale', 'to_scale'],
      buckets: [50, 100, 200, 500, 1000, 2000, 5000],
    });

    this.queryDuration = new Histogram({
      name: 'fractal_query_duration_ms',
      help: 'Database query duration in milliseconds',
      labelNames: ['query_type'],
      buckets: [10, 25, 50, 100, 250, 500, 1000],
    });

    this.cacheHits = new Counter({
      name: 'fractal_cache_hits_total',
      help: 'Total number of cache hits',
      labelNames: ['cache_type'],
    });

    this.cacheMisses = new Counter({
      name: 'fractal_cache_misses_total',
      help: 'Total number of cache misses',
      labelNames: ['cache_type'],
    });

    this.activeViewports = new Gauge({
      name: 'fractal_active_viewports',
      help: 'Number of active viewports',
    });

    this.visibleObjects = new Gauge({
      name: 'fractal_visible_objects',
      help: 'Number of visible objects across all viewports',
      labelNames: ['scale_level'],
    });

    // Register all metrics
    register.registerMetric(this.zoomDuration);
    register.registerMetric(this.queryDuration);
    register.registerMetric(this.cacheHits);
    register.registerMetric(this.cacheMisses);
    register.registerMetric(this.activeViewports);
    register.registerMetric(this.visibleObjects);
  }

  recordZoomTransition(fromScale: number, toScale: number, duration: number): void {
    this.zoomDuration.observe(
      {
        from_scale: this.scaleToLabel(fromScale),
        to_scale: this.scaleToLabel(toScale),
      },
      duration,
    );

    if (duration > 200) {
      this.logger.warn(
        `Slow zoom transition: ${duration}ms from ${fromScale} to ${toScale}`,
      );
    }

    this.eventEmitter.emit('metrics.zoom', {
      fromScale,
      toScale,
      duration,
    });
  }

  recordQueryPerformance(queryType: string, duration: number, resultCount: number): void {
    this.queryDuration.observe({ query_type: queryType }, duration);

    if (duration > 100) {
      this.logger.warn(
        `Slow query: ${queryType} took ${duration}ms for ${resultCount} results`,
      );
    }
  }

  recordCacheHit(cacheType: string): void {
    this.cacheHits.inc({ cache_type: cacheType });
  }

  recordCacheMiss(cacheType: string): void {
    this.cacheMisses.inc({ cache_type: cacheType });
  }

  setActiveViewports(count: number): void {
    this.activeViewports.set(count);
  }

  setVisibleObjects(scale: number, count: number): void {
    this.visibleObjects.set({ scale_level: this.scaleToLabel(scale) }, count);
  }

  getMetrics(): Promise<string> {
    return register.metrics();
  }

  private scaleToLabel(scale: number): string {
    if (scale >= 10) return 'campus';
    if (scale >= 1) return 'building';
    if (scale >= 0.1) return 'floor';
    if (scale >= 0.01) return 'room';
    if (scale >= 0.001) return 'fixture';
    if (scale >= 0.0001) return 'component';
    return 'schematic';
  }
}