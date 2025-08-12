import { Controller, Get, Header } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse } from '@nestjs/swagger';
import { PerformanceMonitorService } from './performance-monitor.service';

@ApiTags('metrics')
@Controller()
export class MetricsController {
  constructor(
    private readonly performanceMonitor: PerformanceMonitorService,
  ) {}

  @Get('metrics')
  @ApiOperation({ summary: 'Get Prometheus metrics' })
  @ApiResponse({
    status: 200,
    description: 'Returns metrics in Prometheus format',
  })
  @Header('Content-Type', 'text/plain')
  async getMetrics(): Promise<string> {
    return this.performanceMonitor.getMetrics();
  }
}