import {
  Entity,
  Column,
  PrimaryGeneratedColumn,
  CreateDateColumn,
  Index,
} from 'typeorm';
import { Polygon } from 'geojson';

export enum MetricType {
  ZOOM_TRANSITION = 'zoom_transition',
  TILE_LOAD = 'tile_load',
  DETAIL_FETCH = 'detail_fetch',
  RENDER_FRAME = 'render_frame',
}

@Entity('performance_metrics', { schema: 'fractal' })
@Index(['metricType', 'createdAt'])
@Index(['userId', 'createdAt'])
export class PerformanceMetric {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({
    name: 'metric_type',
    type: 'enum',
    enum: MetricType,
  })
  metricType: MetricType;

  @Column({ name: 'duration_ms', type: 'decimal', precision: 10, scale: 3 })
  durationMs: number;

  @Column({ name: 'scale_from', type: 'decimal', precision: 10, scale: 8, nullable: true })
  scaleFrom?: number;

  @Column({ name: 'scale_to', type: 'decimal', precision: 10, scale: 8, nullable: true })
  scaleTo?: number;

  @Column({
    name: 'viewport_bounds',
    type: 'geometry',
    spatialFeatureType: 'Polygon',
    srid: 4326,
    nullable: true,
  })
  viewportBounds?: Polygon;

  @Column({ name: 'object_count', type: 'int', nullable: true })
  objectCount?: number;

  @Column({ name: 'user_id', type: 'uuid', nullable: true })
  userId?: string;

  @Column({ name: 'session_id', type: 'uuid', nullable: true })
  sessionId?: string;

  @Column({ name: 'device_memory_gb', type: 'decimal', precision: 4, scale: 2, nullable: true })
  deviceMemoryGb?: number;

  @Column({ name: 'device_cores', type: 'int', nullable: true })
  deviceCores?: number;

  @Column({ name: 'browser_info', type: 'jsonb', nullable: true })
  browserInfo?: Record<string, any>;

  @CreateDateColumn({ name: 'created_at', type: 'timestamptz' })
  createdAt: Date;
}