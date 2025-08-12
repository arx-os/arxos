import { NestFactory } from '@nestjs/core';
import { ValidationPipe } from '@nestjs/common';
import { SwaggerModule, DocumentBuilder } from '@nestjs/swagger';
import { ConfigService } from '@nestjs/config';
import { AppModule } from './app.module';
import { WsAdapter } from '@nestjs/platform-ws';
import * as compression from 'compression';
import { Logger } from '@nestjs/common';

async function bootstrap() {
  const logger = new Logger('Bootstrap');
  
  const app = await NestFactory.create(AppModule, {
    logger: ['error', 'warn', 'log', 'debug', 'verbose'],
  });

  const configService = app.get(ConfigService);
  
  // Enable compression
  app.use(compression());
  
  // Enable CORS
  app.enableCors({
    origin: configService.get('CORS_ORIGIN', '*'),
    credentials: true,
  });
  
  // Global validation pipe
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
      transformOptions: {
        enableImplicitConversion: true,
      },
    }),
  );
  
  // WebSocket adapter
  app.useWebSocketAdapter(new WsAdapter(app));
  
  // Swagger documentation
  const config = new DocumentBuilder()
    .setTitle('Fractal ArxObject Scale Engine')
    .setDescription('Scale-aware rendering and lazy loading for infinite zoom')
    .setVersion('1.0.0')
    .addTag('scale', 'Scale management operations')
    .addTag('viewport', 'Viewport and rendering operations')
    .addTag('tiles', 'Tile-based data loading')
    .addTag('contributions', 'Scale-aware contributions')
    .addBearerAuth()
    .build();
    
  const document = SwaggerModule.createDocument(app, config);
  SwaggerModule.setup('api', app, document);
  
  // Global prefix
  app.setGlobalPrefix('api/v1', {
    exclude: ['health', 'metrics'],
  });
  
  const port = configService.get('PORT', 3000);
  await app.listen(port);
  
  logger.log(`🚀 Scale Engine Service is running on: http://localhost:${port}`);
  logger.log(`📚 Swagger documentation: http://localhost:${port}/api`);
  logger.log(`🔍 Health check: http://localhost:${port}/health`);
  logger.log(`📊 Metrics: http://localhost:${port}/metrics`);
}

bootstrap();