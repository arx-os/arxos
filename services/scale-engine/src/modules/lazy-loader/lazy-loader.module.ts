import { Module } from '@nestjs/common';
import { HttpModule } from '@nestjs/axios';
import { TypeOrmModule } from '@nestjs/typeorm';

import { TileLoaderService } from './tile-loader.service';
import { AdvancedTileLoaderService } from './advanced-tile-loader.service';
import { PredictivePreloaderService } from './predictive-preloader.service';
import { ProgressiveDetailLoaderService } from './progressive-detail-loader.service';

import { TileCache } from '../../entities/tile-cache.entity';
import { ArxObjectDetail } from '../../entities/arxobject-detail.entity';
import { FractalArxObject } from '../../entities/fractal-arxobject.entity';
import { MetricsModule } from '../metrics/metrics.module';
import { PerformanceModule } from '../performance/performance.module';
import { LazyLoaderController } from './lazy-loader.controller';

@Module({
  imports: [
    TypeOrmModule.forFeature([
      TileCache,
      ArxObjectDetail,
      FractalArxObject,
    ]),
    HttpModule.register({
      timeout: 5000,
      maxRedirects: 5,
    }),
    MetricsModule,
    PerformanceModule,
  ],
  controllers: [LazyLoaderController],
  providers: [
    TileLoaderService,
    AdvancedTileLoaderService,
    PredictivePreloaderService,
    ProgressiveDetailLoaderService,
  ],
  exports: [
    TileLoaderService,
    AdvancedTileLoaderService,
    PredictivePreloaderService,
    ProgressiveDetailLoaderService,
  ],
})
export class LazyLoaderModule {}