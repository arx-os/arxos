import {
  Entity,
  Column,
  PrimaryGeneratedColumn,
  ManyToOne,
  JoinColumn,
  CreateDateColumn,
  UpdateDateColumn,
  Index,
} from 'typeorm';
import { FractalArxObject } from './fractal-arxobject.entity';

export enum DetailLevel {
  BASIC = 1,
  STANDARD = 2,
  DETAILED = 3,
  TECHNICAL = 4,
  SCHEMATIC = 5,
}

export enum DetailType {
  VISUAL = 'visual',
  TECHNICAL = 'technical',
  SPECIFICATIONS = 'specifications',
  HISTORY = 'history',
  RELATIONSHIPS = 'relationships',
  SCHEMATIC = 'schematic',
}

@Entity('arxobject_details', { schema: 'fractal' })
@Index(['arxobjectId', 'detailLevel'])
@Index(['detailType'])
@Index(['lastAccessed', 'accessCount'])
export class ArxObjectDetail {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ name: 'arxobject_id', type: 'uuid' })
  arxobjectId: string;

  @ManyToOne(() => FractalArxObject, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'arxobject_id' })
  arxobject: FractalArxObject;

  @Column({
    name: 'detail_level',
    type: 'int',
  })
  detailLevel: DetailLevel;

  @Column({
    name: 'detail_type',
    type: 'enum',
    enum: DetailType,
  })
  detailType: DetailType;

  @Column({ type: 'jsonb' })
  data: Record<string, any>;

  @Column({ name: 'data_size_bytes', type: 'int' })
  dataSizeBytes: number;

  @Column({ name: 'is_compressed', type: 'boolean', default: false })
  isCompressed: boolean;

  @Column({ name: 'compression_type', type: 'varchar', length: 50, nullable: true })
  compressionType?: string;

  @Column({ name: 'storage_url', type: 'text', nullable: true })
  storageUrl?: string;

  @Column({ name: 'last_accessed', type: 'timestamptz', nullable: true })
  lastAccessed?: Date;

  @Column({ name: 'access_count', type: 'int', default: 0 })
  accessCount: number;

  @Column({ name: 'cache_priority', type: 'int', default: 3 })
  cachePriority: number;

  @CreateDateColumn({ name: 'created_at', type: 'timestamptz' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at', type: 'timestamptz' })
  updatedAt: Date;
}