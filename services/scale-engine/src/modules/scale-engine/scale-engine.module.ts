import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';

import { ScaleEngineService } from './scale-engine.service';
import { ScaleEngineController, ViewportController } from './scale-engine.controller';
import { FractalArxObject } from '../../entities/fractal-arxobject.entity';
import { ViewportModule } from '../viewport/viewport.module';
import { MetricsModule } from '../metrics/metrics.module';

@Module({
  imports: [
    TypeOrmModule.forFeature([FractalArxObject]),
    ViewportModule,
    MetricsModule,
  ],
  controllers: [ScaleEngineController, ViewportController],
  providers: [ScaleEngineService],
  exports: [ScaleEngineService],
})
export class ScaleEngineModule {}