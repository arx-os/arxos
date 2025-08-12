import { Module, forwardRef } from '@nestjs/common';
import { ViewportManagerService } from './viewport-manager.service';
import { ScaleEngineModule } from '../scale-engine/scale-engine.module';
import { LazyLoaderModule } from '../lazy-loader/lazy-loader.module';
import { MetricsModule } from '../metrics/metrics.module';

@Module({
  imports: [
    forwardRef(() => ScaleEngineModule),
    LazyLoaderModule,
    MetricsModule,
  ],
  providers: [ViewportManagerService],
  exports: [ViewportManagerService],
})
export class ViewportModule {}