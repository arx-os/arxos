import { Module } from '@nestjs/common';
import { PerformanceBudgetService } from './performance-budget.service';
import { MetricsModule } from '../metrics/metrics.module';

@Module({
  imports: [MetricsModule],
  providers: [PerformanceBudgetService],
  exports: [PerformanceBudgetService],
})
export class PerformanceModule {}