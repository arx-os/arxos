import { ApiProperty } from '@nestjs/swagger';
import { IsNumber, IsOptional, Min, Max, IsInt } from 'class-validator';
import { Type } from 'class-transformer';

export class BoundingBoxDto {
  @ApiProperty({ example: -180, description: 'Minimum X coordinate' })
  @IsNumber()
  @Type(() => Number)
  minX: number;

  @ApiProperty({ example: -90, description: 'Minimum Y coordinate' })
  @IsNumber()
  @Type(() => Number)
  minY: number;

  @ApiProperty({ example: 180, description: 'Maximum X coordinate' })
  @IsNumber()
  @Type(() => Number)
  maxX: number;

  @ApiProperty({ example: 90, description: 'Maximum Y coordinate' })
  @IsNumber()
  @Type(() => Number)
  maxY: number;
}

export class ViewportQueryDto {
  @ApiProperty({
    description: 'Current zoom scale in meters per pixel',
    example: 1.0,
  })
  @IsNumber()
  @Min(0.00001)
  @Max(100)
  @Type(() => Number)
  scale: number;

  @ApiProperty({
    description: 'Detail budget - maximum number of objects to return',
    example: 1000,
    required: false,
  })
  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(10000)
  @Type(() => Number)
  detailBudget?: number;

  @ApiProperty({
    description: 'Minimum importance level (1=critical, 4=optional)',
    example: 3,
    required: false,
  })
  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(4)
  @Type(() => Number)
  importanceFilter?: number;

  @ApiProperty({
    description: 'Filter by object types',
    example: ['BUILDING', 'ROOM'],
    required: false,
  })
  @IsOptional()
  types?: string[];
}

export class ZoomRequestDto {
  @ApiProperty({
    description: 'Target zoom scale',
    example: 0.1,
  })
  @IsNumber()
  @Min(0.00001)
  @Max(100)
  @Type(() => Number)
  targetScale: number;

  @ApiProperty({
    description: 'Focal point X coordinate',
    example: 100000,
  })
  @IsNumber()
  @Type(() => Number)
  focalX: number;

  @ApiProperty({
    description: 'Focal point Y coordinate',
    example: 50000,
  })
  @IsNumber()
  @Type(() => Number)
  focalY: number;

  @ApiProperty({
    description: 'Animation duration in milliseconds',
    example: 200,
    required: false,
  })
  @IsOptional()
  @IsInt()
  @Min(0)
  @Max(1000)
  @Type(() => Number)
  duration?: number;
}

export class TileRequestDto {
  @ApiProperty({ description: 'Tile zoom level', example: 14 })
  @IsInt()
  @Min(0)
  @Max(22)
  @Type(() => Number)
  z: number;

  @ApiProperty({ description: 'Tile X coordinate', example: 8192 })
  @IsInt()
  @Min(0)
  @Type(() => Number)
  x: number;

  @ApiProperty({ description: 'Tile Y coordinate', example: 8192 })
  @IsInt()
  @Min(0)
  @Type(() => Number)
  y: number;

  @ApiProperty({
    description: 'Scale for object filtering',
    example: 1.0,
    required: false,
  })
  @IsOptional()
  @IsNumber()
  @Min(0.00001)
  @Max(100)
  @Type(() => Number)
  scale?: number;
}

export class PreloadRequestDto {
  @ApiProperty({ description: 'Center tile Z', example: 14 })
  @IsInt()
  @Min(0)
  @Max(22)
  @Type(() => Number)
  centerZ: number;

  @ApiProperty({ description: 'Center tile X', example: 8192 })
  @IsInt()
  @Min(0)
  @Type(() => Number)
  centerX: number;

  @ApiProperty({ description: 'Center tile Y', example: 8192 })
  @IsInt()
  @Min(0)
  @Type(() => Number)
  centerY: number;

  @ApiProperty({
    description: 'Radius of tiles to preload',
    example: 2,
    required: false,
  })
  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(5)
  @Type(() => Number)
  radius?: number;

  @ApiProperty({
    description: 'Scale for preloading',
    example: 1.0,
  })
  @IsNumber()
  @Min(0.00001)
  @Max(100)
  @Type(() => Number)
  scale: number;
}