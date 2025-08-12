import {
  Controller,
  Get,
  Post,
  Query,
  Body,
  Param,
  UseGuards,
  HttpStatus,
} from '@nestjs/common';
import {
  ApiTags,
  ApiOperation,
  ApiResponse,
  ApiBearerAuth,
  ApiQuery,
} from '@nestjs/swagger';
import { ThrottlerGuard } from '@nestjs/throttler';

import { ScaleEngineService } from './scale-engine.service';
import { ViewportManagerService } from '../viewport/viewport-manager.service';
import {
  BoundingBoxDto,
  ViewportQueryDto,
  ZoomRequestDto,
  TileRequestDto,
  PreloadRequestDto,
} from '../../dto/viewport.dto';
import { FractalArxObject } from '../../entities/fractal-arxobject.entity';

@ApiTags('scale')
@Controller('scale')
@UseGuards(ThrottlerGuard)
export class ScaleEngineController {
  constructor(
    private readonly scaleEngine: ScaleEngineService,
    private readonly viewportManager: ViewportManagerService,
  ) {}

  @Get('visible-objects')
  @ApiOperation({ summary: 'Get visible objects for viewport and scale' })
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'Returns visible objects within viewport at specified scale',
    type: [FractalArxObject],
  })
  @ApiQuery({ name: 'minX', type: Number, required: true })
  @ApiQuery({ name: 'minY', type: Number, required: true })
  @ApiQuery({ name: 'maxX', type: Number, required: true })
  @ApiQuery({ name: 'maxY', type: Number, required: true })
  @ApiQuery({ name: 'scale', type: Number, required: true })
  @ApiQuery({ name: 'detailBudget', type: Number, required: false })
  @ApiQuery({ name: 'importanceFilter', type: Number, required: false })
  @ApiQuery({ name: 'types', type: [String], required: false })
  async getVisibleObjects(
    @Query() viewport: BoundingBoxDto,
    @Query() query: ViewportQueryDto,
  ): Promise<FractalArxObject[]> {
    return this.scaleEngine.getVisibleObjects(viewport, query);
  }

  @Get('children/:parentId')
  @ApiOperation({ summary: 'Get child objects at specific scale' })
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'Returns child objects of parent at specified scale',
    type: [FractalArxObject],
  })
  async getChildren(
    @Param('parentId') parentId: string,
    @Query('scale') scale: number,
    @Query('limit') limit?: number,
  ): Promise<FractalArxObject[]> {
    return this.scaleEngine.materializeChildren(parentId, scale, limit);
  }

  @Get('scale-breaks')
  @ApiOperation({ summary: 'Get natural scale break points' })
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'Returns array of scale values for smooth transitions',
    type: [Number],
  })
  getScaleBreaks(): number[] {
    return this.scaleEngine.getScaleBreaks();
  }

  @Get('snap-scale/:scale')
  @ApiOperation({ summary: 'Snap to nearest meaningful scale level' })
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'Returns nearest meaningful scale value',
    type: Number,
  })
  snapToScale(@Param('scale') scale: number): number {
    return this.scaleEngine.snapToNearestScale(scale);
  }

  @Get('detail-level/:scale')
  @ApiOperation({ summary: 'Get appropriate detail level for scale' })
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'Returns detail level (1-5) for given scale',
    type: Number,
  })
  getDetailLevel(@Param('scale') scale: number): number {
    return this.scaleEngine.getDetailLevelForScale(scale);
  }

  @Get('statistics')
  @ApiOperation({ summary: 'Get scale statistics for monitoring' })
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'Returns statistics about objects at different scales',
  })
  @ApiQuery({ name: 'minX', type: Number, required: false })
  @ApiQuery({ name: 'minY', type: Number, required: false })
  @ApiQuery({ name: 'maxX', type: Number, required: false })
  @ApiQuery({ name: 'maxY', type: Number, required: false })
  async getStatistics(
    @Query() viewport?: BoundingBoxDto,
  ): Promise<any> {
    return this.scaleEngine.getScaleStatistics(viewport);
  }

  @Get('detail-budget')
  @ApiOperation({ summary: 'Calculate detail budget for device' })
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'Returns recommended detail budget based on device capabilities',
    type: Number,
  })
  @ApiQuery({ name: 'deviceMemory', type: Number, required: false })
  @ApiQuery({ name: 'deviceCores', type: Number, required: false })
  calculateDetailBudget(
    @Query('deviceMemory') deviceMemory?: number,
    @Query('deviceCores') deviceCores?: number,
  ): number {
    return this.scaleEngine.calculateDetailBudget(deviceMemory, deviceCores);
  }

  @Post('prefetch')
  @ApiOperation({ summary: 'Prefetch area for predicted navigation' })
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'Prefetches objects in background',
  })
  async prefetchArea(
    @Body() request: {
      center: { x: number; y: number };
      radius: number;
      scale: number;
    },
  ): Promise<{ status: string }> {
    await this.scaleEngine.prefetchArea(
      request.center,
      request.radius,
      request.scale,
    );
    return { status: 'prefetching' };
  }
}

@ApiTags('viewport')
@Controller('viewport')
@UseGuards(ThrottlerGuard)
export class ViewportController {
  constructor(
    private readonly viewportManager: ViewportManagerService,
  ) {}

  @Post('initialize')
  @ApiOperation({ summary: 'Initialize viewport with starting position' })
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'Viewport initialized successfully',
  })
  async initialize(
    @Body() request: {
      center: { x: number; y: number };
      scale: number;
      viewportSize: { width: number; height: number };
    },
  ): Promise<{ status: string; objectCount: number }> {
    await this.viewportManager.initialize(
      request.center,
      request.scale,
      request.viewportSize,
    );
    
    const state = this.viewportManager.getState();
    return {
      status: 'initialized',
      objectCount: state.visibleObjects.size,
    };
  }

  @Post('zoom')
  @ApiOperation({ summary: 'Zoom to target scale with animation' })
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'Zoom completed successfully',
  })
  async zoom(
    @Body() request: ZoomRequestDto,
  ): Promise<{ status: string; scale: number; objectCount: number }> {
    await this.viewportManager.zoomTo(request);
    
    const state = this.viewportManager.getState();
    return {
      status: 'zoomed',
      scale: state.scale,
      objectCount: state.visibleObjects.size,
    };
  }

  @Post('pan')
  @ApiOperation({ summary: 'Pan viewport to new center' })
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'Pan completed successfully',
  })
  async pan(
    @Body() request: {
      center: { x: number; y: number };
      duration?: number;
    },
  ): Promise<{ status: string; objectCount: number }> {
    await this.viewportManager.panTo(request.center, request.duration);
    
    const state = this.viewportManager.getState();
    return {
      status: 'panned',
      objectCount: state.visibleObjects.size,
    };
  }

  @Get('state')
  @ApiOperation({ summary: 'Get current viewport state' })
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'Returns current viewport state',
  })
  getState(): any {
    const state = this.viewportManager.getState();
    return {
      viewport: state.viewport,
      scale: state.scale,
      center: state.center,
      objectCount: state.visibleObjects.size,
      loadingTiles: state.loadingTiles.size,
    };
  }

  @Get('objects')
  @ApiOperation({ summary: 'Get currently visible objects' })
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'Returns array of visible objects',
    type: [FractalArxObject],
  })
  getVisibleObjects(): FractalArxObject[] {
    return this.viewportManager.getVisibleObjects();
  }
}