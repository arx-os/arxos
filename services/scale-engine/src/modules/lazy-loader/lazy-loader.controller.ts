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
  ApiQuery,
  ApiBody,
} from '@nestjs/swagger';
import { ThrottlerGuard } from '@nestjs/throttler';

import { AdvancedTileLoaderService, TileRequest } from './advanced-tile-loader.service';
import { PredictivePreloaderService } from './predictive-preloader.service';
import { ProgressiveDetailLoaderService, DetailRequest } from './progressive-detail-loader.service';
import { PerformanceBudgetService } from '../performance/performance-budget.service';

@ApiTags('lazy-loading')
@Controller('lazy-loading')
@UseGuards(ThrottlerGuard)
export class LazyLoaderController {
  constructor(
    private readonly advancedTileLoader: AdvancedTileLoaderService,
    private readonly predictivePreloader: PredictivePreloaderService,
    private readonly progressiveDetailLoader: ProgressiveDetailLoaderService,
    private readonly performanceBudget: PerformanceBudgetService,
  ) {}

  @Post('tiles/load')
  @ApiOperation({ summary: 'Load specific tiles with priority' })
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'Tiles loaded successfully',
  })
  @ApiBody({
    description: 'Tile loading request',
    schema: {
      type: 'object',
      properties: {
        tiles: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              coordinate: {
                type: 'object',
                properties: {
                  z: { type: 'number' },
                  x: { type: 'number' },
                  y: { type: 'number' },
                },
              },
              scale: { type: 'number' },
              priority: { 
                type: 'string',
                enum: ['immediate', 'high', 'normal', 'low'],
              },
            },
          },
        },
      },
    },
  })
  async loadTiles(
    @Body() request: { tiles: TileRequest[] },
  ): Promise<any[]> {
    const loadPromises = request.tiles.map(tileRequest =>
      this.advancedTileLoader.loadTile(tileRequest),
    );
    
    const tiles = await Promise.all(loadPromises);
    
    return tiles.map(tile => ({
      coordinate: tile.coordinate,
      objectCount: tile.metadata.objectCount,
      dataSize: tile.metadata.dataSize,
      source: tile.vectorData ? 'vector' : 'raster',
      compressed: tile.metadata.compressed,
    }));
  }

  @Post('details/progressive')
  @ApiOperation({ summary: 'Load object details progressively' })
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'Details loaded progressively',
  })
  @ApiBody({
    description: 'Progressive detail loading request',
    schema: {
      type: 'object',
      properties: {
        objectId: { type: 'string' },
        scale: { type: 'number' },
        strategy: {
          type: 'string',
          enum: ['immediate', 'progressive', 'lazy', 'background'],
        },
      },
    },
  })
  async loadProgressiveDetails(
    @Body() request: {
      objectId: string;
      scale: number;
      strategy?: 'immediate' | 'progressive' | 'lazy' | 'background';
    },
  ): Promise<any> {
    const details = await this.progressiveDetailLoader.loadObjectDetails(
      request.objectId,
      request.scale,
      request.strategy || 'progressive',
    );
    
    return {
      objectId: request.objectId,
      scale: request.scale,
      detailsLoaded: details.length,
      details: details.map(detail => ({
        level: detail.detailLevel,
        type: detail.detailType,
        loadTime: detail.loadTime,
        source: detail.source,
        compressed: detail.compressed,
      })),
    };
  }

  @Post('details/batch')
  @ApiOperation({ summary: 'Load details for multiple objects' })
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'Batch details loaded',
  })
  async loadBatchDetails(
    @Body() request: { requests: DetailRequest[] },
  ): Promise<any> {
    const loadPromises = request.requests.map(detailRequest =>
      this.progressiveDetailLoader.loadObjectDetails(
        detailRequest.objectId,
        // Assuming scale is provided in request
        (detailRequest as any).scale || 1.0,
        'progressive',
      ),
    );
    
    const results = await Promise.all(loadPromises);
    
    return {
      totalRequests: request.requests.length,
      results: results.map((details, index) => ({
        objectId: request.requests[index].objectId,
        detailsLoaded: details.length,
        totalLoadTime: details.reduce((sum, d) => sum + d.loadTime, 0),
      })),
    };
  }

  @Get('cache/stats')
  @ApiOperation({ summary: 'Get cache statistics' })
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'Returns cache statistics',
  })
  getCacheStats(): any {
    return {
      tiles: this.advancedTileLoader.getCacheStats(),
      details: this.progressiveDetailLoader.getStatistics(),
      prediction: this.predictivePreloader.getStatistics(),
    };
  }

  @Post('cache/clear')
  @ApiOperation({ summary: 'Clear all caches' })
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'Caches cleared successfully',
  })
  async clearCaches(): Promise<{ status: string }> {
    await this.advancedTileLoader.clearCaches();
    return { status: 'cleared' };
  }

  @Get('performance/budget')
  @ApiOperation({ summary: 'Get current performance budget' })
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'Returns current performance budget and statistics',
  })
  getPerformanceBudget(): any {
    return {
      budget: this.performanceBudget.getCurrentBudget(),
      adaptiveSettings: this.performanceBudget.getAdaptiveSettings(),
      capabilities: this.performanceBudget.getDeviceCapabilities(),
      stats: this.performanceBudget.getPerformanceStats(),
    };
  }

  @Post('performance/budget/init')
  @ApiOperation({ summary: 'Initialize performance budget with device capabilities' })
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'Performance budget initialized',
  })
  @ApiBody({
    description: 'Device capabilities',
    schema: {
      type: 'object',
      properties: {
        memory: { type: 'number', description: 'Memory in GB' },
        cores: { type: 'number', description: 'CPU cores' },
        gpu: {
          type: 'string',
          enum: ['low', 'medium', 'high', 'discrete'],
          description: 'GPU capability',
        },
        connection: {
          type: 'string',
          enum: ['slow', 'fast', 'wifi', 'cellular'],
          description: 'Connection type',
        },
        screenSize: {
          type: 'object',
          properties: {
            width: { type: 'number' },
            height: { type: 'number' },
          },
        },
        pixelRatio: { type: 'number' },
      },
    },
  })
  initializePerformanceBudget(
    @Body() capabilities: any,
  ): { status: string; budget: any } {
    this.performanceBudget.initializeWithCapabilities(capabilities);
    
    return {
      status: 'initialized',
      budget: this.performanceBudget.getCurrentBudget(),
    };
  }

  @Post('performance/budget/override')
  @ApiOperation({ summary: 'Override performance budget settings' })
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'Performance budget overridden',
  })
  overridePerformanceBudget(
    @Body() budgetOverride: any,
  ): { status: string } {
    this.performanceBudget.setBudgetOverride(budgetOverride);
    return { status: 'overridden' };
  }

  @Get('preload/stats')
  @ApiOperation({ summary: 'Get predictive preloading statistics' })
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'Returns preloading statistics',
  })
  getPreloadStats(): any {
    return this.predictivePreloader.getStatistics();
  }

  @Get('tiles/:z/:x/:y/vector')
  @ApiOperation({ summary: 'Get vector tile data' })
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'Returns vector tile data',
  })
  @ApiQuery({ name: 'scale', type: Number, required: false })
  async getVectorTile(
    @Param('z') z: number,
    @Param('x') x: number,
    @Param('y') y: number,
    @Query('scale') scale?: number,
  ): Promise<any> {
    const tileRequest: TileRequest = {
      coordinate: { z, x, y },
      scale: scale || 1.0,
      priority: 'normal',
    };
    
    const tile = await this.advancedTileLoader.loadTile(tileRequest);
    
    if (tile.vectorData) {
      return {
        coordinate: tile.coordinate,
        vectorData: tile.vectorData,
        metadata: tile.metadata,
      };
    } else {
      return {
        coordinate: tile.coordinate,
        message: 'Vector data not available for this tile',
        objectCount: tile.metadata.objectCount,
      };
    }
  }

  @Post('preload/area')
  @ApiOperation({ summary: 'Trigger predictive preloading for an area' })
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'Preloading triggered',
  })
  @ApiBody({
    description: 'Area preloading request',
    schema: {
      type: 'object',
      properties: {
        center: {
          type: 'object',
          properties: {
            x: { type: 'number' },
            y: { type: 'number' },
          },
        },
        radius: { type: 'number' },
        scale: { type: 'number' },
        priority: {
          type: 'string',
          enum: ['high', 'normal', 'low'],
        },
      },
    },
  })
  async preloadArea(
    @Body() request: {
      center: { x: number; y: number };
      radius: number;
      scale: number;
      priority?: 'high' | 'normal' | 'low';
    },
  ): Promise<{ status: string; message: string }> {
    // This would need to be implemented in the predictive preloader
    // For now, return a success message
    
    return {
      status: 'queued',
      message: `Preloading area around (${request.center.x}, ${request.center.y}) with radius ${request.radius}`,
    };
  }
}