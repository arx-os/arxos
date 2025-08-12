import {
  Entity,
  Column,
  PrimaryGeneratedColumn,
  ManyToOne,
  JoinColumn,
  CreateDateColumn,
  UpdateDateColumn,
  Index,
  Check,
} from 'typeorm';
import { ApiProperty } from '@nestjs/swagger';
import { FractalArxObject } from './fractal-arxobject.entity';

@Entity('visibility_rules', { schema: 'fractal' })
@Index(['arxobjectId'])
@Index(['minZoom', 'maxZoom'])
@Check('"min_zoom" <= "max_zoom"')
export class VisibilityRule {
  @ApiProperty()
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @ApiProperty()
  @Column({ name: 'arxobject_id', type: 'uuid' })
  arxobjectId: string;

  @ManyToOne(() => FractalArxObject, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'arxobject_id' })
  arxobject: FractalArxObject;

  @ApiProperty({ example: 0.5, description: 'Minimum zoom level where object is visible' })
  @Column({ name: 'min_zoom', type: 'decimal', precision: 10, scale: 8 })
  minZoom: number;

  @ApiProperty({ example: 20.0, description: 'Maximum zoom level where object is visible' })
  @Column({ name: 'max_zoom', type: 'decimal', precision: 10, scale: 8 })
  maxZoom: number;

  @ApiProperty({
    example: { shape: 'box', color: '#4A90E2', opacity: 0.8 },
    description: 'Style overrides at different scales',
  })
  @Column({ name: 'render_style', type: 'jsonb', default: {} })
  renderStyle: Record<string, any>;

  @ApiProperty({
    example: 0,
    description: 'Level of detail simplification (0=full detail)',
  })
  @Column({ name: 'simplification_level', type: 'int', default: 0 })
  simplificationLevel: number;

  @ApiProperty({ example: 1.0, description: 'Opacity from 0 to 1' })
  @Column({ type: 'decimal', precision: 3, scale: 2, default: 1.0 })
  opacity: number;

  @ApiProperty({
    example: 'importance_level <= 2',
    description: 'SQL expression for dynamic visibility',
  })
  @Column({ name: 'condition_expression', type: 'text', nullable: true })
  conditionExpression?: string;

  @ApiProperty()
  @CreateDateColumn({ name: 'created_at', type: 'timestamptz' })
  createdAt: Date;

  @ApiProperty()
  @UpdateDateColumn({ name: 'updated_at', type: 'timestamptz' })
  updatedAt: Date;

  // Helper methods
  isVisibleAtZoom(zoom: number): boolean {
    return zoom >= this.minZoom && zoom <= this.maxZoom;
  }

  getStyleForZoom(zoom: number): Record<string, any> {
    if (!this.isVisibleAtZoom(zoom)) {
      return { display: 'none' };
    }

    const baseStyle = { ...this.renderStyle };
    
    // Apply opacity
    if (this.opacity < 1) {
      baseStyle.opacity = this.opacity;
    }

    // Apply simplification based on zoom
    const zoomRange = this.maxZoom - this.minZoom;
    const zoomPosition = (zoom - this.minZoom) / zoomRange;
    
    if (zoomPosition < 0.3 && this.simplificationLevel > 0) {
      baseStyle.simplified = true;
      baseStyle.simplificationLevel = this.simplificationLevel;
    }

    return baseStyle;
  }
}