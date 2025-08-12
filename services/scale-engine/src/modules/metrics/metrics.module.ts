import { Module } from '@nestjs/common';
import { PerformanceMonitorService } from './performance-monitor.service';
import { MetricsController } from './metrics.controller';

@Module({
  providers: [PerformanceMonitorService],
  controllers: [MetricsController],
  exports: [PerformanceMonitorService],
})
export class MetricsModule {}