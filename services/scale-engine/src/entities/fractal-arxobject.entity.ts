import {
  Entity,
  Column,
  PrimaryGeneratedColumn,
  ManyToOne,
  OneToMany,
  JoinColumn,
  CreateDateColumn,
  UpdateDateColumn,
  Index,
  Check,
} from 'typeorm';
import { ApiProperty } from '@nestjs/swagger';
import { Point } from 'geojson';

export enum ImportanceLevel {
  CRITICAL = 1,
  IMPORTANT = 2,
  DETAIL = 3,
  OPTIONAL = 4,
}

@Entity('fractal_arxobjects', { schema: 'fractal' })
@Index(['minScale', 'maxScale'])
@Index(['optimalScale'])
@Index(['importanceLevel', 'optimalScale'])
@Index(['objectType', 'optimalScale'])
@Check('"min_scale" <= "optimal_scale" AND "optimal_scale" <= "max_scale"')
export class FractalArxObject {
  @ApiProperty({ example: 'a0000000-0000-0000-0000-000000000001' })
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @ApiProperty({ required: false })
  @Column({ name: 'parent_id', type: 'uuid', nullable: true })
  parentId?: string;

  @ManyToOne(() => FractalArxObject, (object) => object.children, {
    nullable: true,
    onDelete: 'CASCADE',
  })
  @JoinColumn({ name: 'parent_id' })
  parent?: FractalArxObject;

  @OneToMany(() => FractalArxObject, (object) => object.parent)
  children?: FractalArxObject[];

  @ApiProperty({ example: 'BUILDING' })
  @Column({ name: 'object_type', type: 'varchar', length: 255 })
  objectType: string;

  @ApiProperty({ required: false })
  @Column({ name: 'object_subtype', type: 'varchar', length: 255, nullable: true })
  objectSubtype?: string;

  @ApiProperty({ example: 'Engineering Building' })
  @Column({ type: 'varchar', length: 500, nullable: true })
  name?: string;

  @ApiProperty()
  @Column({ type: 'text', nullable: true })
  description?: string;

  @ApiProperty({ example: 100000 })
  @Column({ name: 'position_x', type: 'decimal', precision: 15, scale: 9 })
  positionX: number;

  @ApiProperty({ example: 50000 })
  @Column({ name: 'position_y', type: 'decimal', precision: 15, scale: 9 })
  positionY: number;

  @ApiProperty({ example: 0 })
  @Column({ name: 'position_z', type: 'decimal', precision: 15, scale: 9, default: 0 })
  positionZ: number;

  @ApiProperty({ example: 0 })
  @Column({ name: 'rotation_x', type: 'decimal', precision: 7, scale: 4, default: 0 })
  rotationX: number;

  @ApiProperty({ example: 0 })
  @Column({ name: 'rotation_y', type: 'decimal', precision: 7, scale: 4, default: 0 })
  rotationY: number;

  @ApiProperty({ example: 0 })
  @Column({ name: 'rotation_z', type: 'decimal', precision: 7, scale: 4, default: 0 })
  rotationZ: number;

  @ApiProperty({ example: 0.5, description: 'Minimum scale in meters/pixel' })
  @Column({ name: 'min_scale', type: 'decimal', precision: 10, scale: 8 })
  minScale: number;

  @ApiProperty({ example: 20.0, description: 'Maximum scale in meters/pixel' })
  @Column({ name: 'max_scale', type: 'decimal', precision: 10, scale: 8 })
  maxScale: number;

  @ApiProperty({ example: 1.0, description: 'Optimal viewing scale in meters/pixel' })
  @Column({ name: 'optimal_scale', type: 'decimal', precision: 10, scale: 8 })
  optimalScale: number;

  @ApiProperty({ enum: ImportanceLevel, example: ImportanceLevel.IMPORTANT })
  @Column({
    name: 'importance_level',
    type: 'int',
    default: ImportanceLevel.DETAIL,
  })
  importanceLevel: ImportanceLevel;

  @ApiProperty({ example: 80000, description: 'Width in millimeters' })
  @Column({ type: 'decimal', precision: 10, scale: 6, nullable: true })
  width?: number;

  @ApiProperty({ example: 60000, description: 'Height in millimeters' })
  @Column({ type: 'decimal', precision: 10, scale: 6, nullable: true })
  height?: number;

  @ApiProperty({ example: 20000, description: 'Depth in millimeters' })
  @Column({ type: 'decimal', precision: 10, scale: 6, nullable: true })
  depth?: number;

  @ApiProperty({ example: { floors: 5, year_built: 2010 } })
  @Column({ type: 'jsonb', default: {} })
  properties: Record<string, any>;

  @ApiProperty({ example: ['educational', 'accessible'] })
  @Column({ type: 'text', array: true, default: [] })
  tags: string[];

  @ApiProperty()
  @Column({ type: 'int', default: 1 })
  version: number;

  @ApiProperty()
  @Column({ name: 'created_by', type: 'uuid' })
  createdBy: string;

  @ApiProperty()
  @Column({ name: 'updated_by', type: 'uuid', nullable: true })
  updatedBy?: string;

  @ApiProperty()
  @CreateDateColumn({ name: 'created_at', type: 'timestamptz' })
  createdAt: Date;

  @ApiProperty()
  @UpdateDateColumn({ name: 'updated_at', type: 'timestamptz' })
  updatedAt: Date;

  @Column({
    type: 'geometry',
    spatialFeatureType: 'Point',
    srid: 4326,
    nullable: true,
  })
  geom?: Point;

  // Virtual properties for calculations
  get distanceFromOptimal(): (scale: number) => number {
    return (scale: number) => Math.abs(this.optimalScale - scale);
  }

  get isVisibleAtScale(): (scale: number) => boolean {
    return (scale: number) => scale >= this.minScale && scale <= this.maxScale;
  }

  get center(): { x: number; y: number; z: number } {
    return {
      x: Number(this.positionX),
      y: Number(this.positionY),
      z: Number(this.positionZ),
    };
  }

  get bounds(): { min: Point; max: Point } | null {
    if (!this.width || !this.height) return null;
    
    const halfWidth = Number(this.width) / 2;
    const halfHeight = Number(this.height) / 2;
    
    return {
      min: {
        type: 'Point',
        coordinates: [
          Number(this.positionX) - halfWidth,
          Number(this.positionY) - halfHeight,
          Number(this.positionZ),
        ],
      },
      max: {
        type: 'Point',
        coordinates: [
          Number(this.positionX) + halfWidth,
          Number(this.positionY) + halfHeight,
          Number(this.positionZ) + (this.depth ? Number(this.depth) : 0),
        ],
      },
    };
  }
}