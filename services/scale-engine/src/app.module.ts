import { Module } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';
import { CacheModule } from '@nestjs/cache-manager';
import { ThrottlerModule } from '@nestjs/throttler';
import { redisStore } from 'cache-manager-redis-store';

import { ScaleEngineModule } from './modules/scale-engine/scale-engine.module';
import { ViewportModule } from './modules/viewport/viewport.module';
import { LazyLoaderModule } from './modules/lazy-loader/lazy-loader.module';
import { ContributionModule } from './modules/contribution/contribution.module';
import { HealthModule } from './modules/health/health.module';
import { MetricsModule } from './modules/metrics/metrics.module';
import { WebSocketModule } from './modules/websocket/websocket.module';

import configuration from './config/configuration';
import { FractalArxObject } from './entities/fractal-arxobject.entity';
import { VisibilityRule } from './entities/visibility-rule.entity';
import { ScaleContribution } from './entities/scale-contribution.entity';
import { ArxObjectDetail } from './entities/arxobject-detail.entity';
import { TileCache } from './entities/tile-cache.entity';
import { PerformanceMetric } from './entities/performance-metric.entity';

@Module({
  imports: [
    // Configuration
    ConfigModule.forRoot({
      isGlobal: true,
      load: [configuration],
      envFilePath: ['.env.local', '.env'],
    }),
    
    // Database
    TypeOrmModule.forRootAsync({
      imports: [ConfigModule],
      useFactory: (configService: ConfigService) => ({
        type: 'postgres',
        host: configService.get('database.host'),
        port: configService.get('database.port'),
        username: configService.get('database.username'),
        password: configService.get('database.password'),
        database: configService.get('database.name'),
        schema: 'fractal',
        entities: [
          FractalArxObject,
          VisibilityRule,
          ScaleContribution,
          ArxObjectDetail,
          TileCache,
          PerformanceMetric,
        ],
        synchronize: false, // Use migrations in production
        logging: configService.get('database.logging'),
        poolSize: configService.get('database.poolSize', 10),
        extra: {
          max: configService.get('database.poolSize', 10),
          connectionTimeoutMillis: 5000,
        },
      }),
      inject: [ConfigService],
    }),
    
    // Cache
    CacheModule.registerAsync({
      isGlobal: true,
      imports: [ConfigModule],
      useFactory: async (configService: ConfigService) => ({
        store: await redisStore({
          socket: {
            host: configService.get('redis.host'),
            port: configService.get('redis.port'),
          },
          password: configService.get('redis.password'),
          ttl: configService.get('cache.ttl', 300),
        }),
      }),
      inject: [ConfigService],
    }),
    
    // Rate limiting
    ThrottlerModule.forRoot([{
      ttl: 60000, // 1 minute
      limit: 100, // 100 requests per minute
    }]),
    
    // Feature modules
    ScaleEngineModule,
    ViewportModule,
    LazyLoaderModule,
    ContributionModule,
    HealthModule,
    MetricsModule,
    WebSocketModule,
  ],
})
export class AppModule {}