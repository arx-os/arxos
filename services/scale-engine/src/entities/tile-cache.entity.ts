import {
  Entity,
  Column,
  PrimaryColumn,
  CreateDateColumn,
  Index,
} from 'typeorm';
import { Polygon } from 'geojson';

@Entity('tile_cache', { schema: 'fractal' })
@Index(['expiresAt'])
export class TileCache {
  @PrimaryColumn({ type: 'int' })
  z: number;

  @PrimaryColumn({ type: 'int' })
  x: number;

  @PrimaryColumn({ type: 'int' })
  y: number;

  @Column({ type: 'decimal', precision: 10, scale: 8 })
  scale: number;

  @Column({
    type: 'geometry',
    spatialFeatureType: 'Polygon',
    srid: 4326,
  })
  bounds: Polygon;

  @Column({ name: 'object_count', type: 'int' })
  objectCount: number;

  @Column({ type: 'jsonb' })
  objects: any[];

  @CreateDateColumn({ name: 'created_at', type: 'timestamptz' })
  createdAt: Date;

  @Column({ name: 'expires_at', type: 'timestamptz' })
  expiresAt: Date;

  @Column({ name: 'hit_count', type: 'int', default: 0 })
  hitCount: number;

  @Column({ name: 'last_hit', type: 'timestamptz', nullable: true })
  lastHit?: Date;
}