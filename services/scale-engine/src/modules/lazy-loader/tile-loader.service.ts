import { Injectable, Logger } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { ConfigService } from '@nestjs/config';
import { Cache } from 'cache-manager';
import { Inject } from '@nestjs/common';
import { CACHE_MANAGER } from '@nestjs/cache-manager';
import { firstValueFrom } from 'rxjs';

export interface Tile {
  x: number;
  y: number;
  z: number;
}

export interface TileData {
  tile: Tile;
  bounds: {
    minX: number;
    minY: number;
    maxX: number;
    maxY: number;
  };
  objects: any[];
  count: number;
}

@Injectable()
export class TileLoaderService {
  private readonly logger = new Logger(TileLoaderService.name);
  private readonly tileServerUrl: string;
  private readonly tileSize: number;

  constructor(
    private readonly httpService: HttpService,
    @Inject(CACHE_MANAGER) private cacheManager: Cache,
    private readonly configService: ConfigService,
  ) {
    this.tileServerUrl = this.configService.get('tileServer.url', 'http://tile-server:8080');
    this.tileSize = this.configService.get('viewport.tileSize', 256);
  }

  async loadTile(tile: Tile, scale: number): Promise<TileData> {
    const cacheKey = `tile:${tile.z}:${tile.x}:${tile.y}:${scale}`;
    
    // Check cache
    const cached = await this.cacheManager.get<TileData>(cacheKey);
    if (cached) {
      return cached;
    }
    
    try {
      // Fetch from tile server
      const url = `${this.tileServerUrl}/tiles/${tile.z}/${tile.x}/${tile.y}?scale=${scale}`;
      const response = await firstValueFrom(
        this.httpService.get<TileData>(url)
      );
      
      const tileData = response.data;
      
      // Cache the result
      await this.cacheManager.set(cacheKey, tileData, 300000); // 5 minutes
      
      return tileData;
    } catch (error) {
      this.logger.error(`Failed to load tile ${tile.z}/${tile.x}/${tile.y}`, error);
      
      // Return empty tile on error
      return {
        tile,
        bounds: this.calculateTileBounds(tile),
        objects: [],
        count: 0,
      };
    }
  }

  private calculateTileBounds(tile: Tile) {
    const tileSize = 360 / Math.pow(2, tile.z);
    return {
      minX: tile.x * tileSize - 180,
      maxX: (tile.x + 1) * tileSize - 180,
      minY: tile.y * tileSize - 90,
      maxY: (tile.y + 1) * tileSize - 90,
    };
  }
}