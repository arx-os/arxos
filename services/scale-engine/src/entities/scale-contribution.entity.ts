import {
  Entity,
  Column,
  PrimaryGeneratedColumn,
  ManyToOne,
  JoinColumn,
  CreateDateColumn,
  Index,
} from 'typeorm';
import { FractalArxObject } from './fractal-arxobject.entity';

export enum ContributionType {
  GEOMETRY = 'geometry',
  SPECIFICATION = 'specification',
  SCHEMATIC = 'schematic',
  MODIFICATION = 'modification',
  VALIDATION = 'validation',
  PHOTO = 'photo',
  MEASUREMENT = 'measurement',
  MATERIAL = 'material',
  CONNECTION = 'connection',
}

export enum ValidationStatus {
  PENDING = 'pending',
  VALIDATED = 'validated',
  DISPUTED = 'disputed',
  REJECTED = 'rejected',
}

@Entity('scale_contributions', { schema: 'fractal' })
@Index(['arxobjectId'])
@Index(['contributionScale'])
@Index(['contributionType', 'contributionScale'])
@Index(['contributorId', 'createdAt'])
export class ScaleContribution {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ name: 'arxobject_id', type: 'uuid' })
  arxobjectId: string;

  @ManyToOne(() => FractalArxObject, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'arxobject_id' })
  arxobject: FractalArxObject;

  @Column({ name: 'contributor_id', type: 'uuid' })
  contributorId: string;

  @Column({ name: 'contribution_scale', type: 'decimal', precision: 10, scale: 8 })
  contributionScale: number;

  @Column({
    name: 'contribution_type',
    type: 'enum',
    enum: ContributionType,
  })
  contributionType: ContributionType;

  @Column({ type: 'jsonb' })
  data: Record<string, any>;

  @Column({ type: 'text', array: true, nullable: true })
  attachments?: string[];

  @Column({
    name: 'confidence_score',
    type: 'decimal',
    precision: 3,
    scale: 2,
    default: 0.5,
  })
  confidenceScore: number;

  @Column({ name: 'peer_validations', type: 'int', default: 0 })
  peerValidations: number;

  @Column({
    name: 'validation_status',
    type: 'enum',
    enum: ValidationStatus,
    default: ValidationStatus.PENDING,
  })
  validationStatus: ValidationStatus;

  @Column({ name: 'bilt_earned', type: 'decimal', precision: 18, scale: 8, nullable: true })
  biltEarned?: number;

  @Column({ name: 'bilt_paid', type: 'boolean', default: false })
  biltPaid: boolean;

  @CreateDateColumn({ name: 'created_at', type: 'timestamptz' })
  createdAt: Date;

  @Column({ name: 'validated_at', type: 'timestamptz', nullable: true })
  validatedAt?: Date;

  @Column({ name: 'validated_by', type: 'uuid', nullable: true })
  validatedBy?: string;
}