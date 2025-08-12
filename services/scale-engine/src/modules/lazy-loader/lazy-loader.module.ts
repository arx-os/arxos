import { Module } from '@nestjs/common';
import { HttpModule } from '@nestjs/axios';
import { TileLoaderService } from './tile-loader.service';

@Module({
  imports: [
    HttpModule.register({
      timeout: 5000,
      maxRedirects: 5,
    }),
  ],
  providers: [TileLoaderService],
  exports: [TileLoaderService],
})
export class LazyLoaderModule {}