export default () => ({
  port: parseInt(process.env.PORT, 10) || 3000,
  
  database: {
    host: process.env.DATABASE_HOST || 'localhost',
    port: parseInt(process.env.DATABASE_PORT, 10) || 5433,
    username: process.env.DATABASE_USER || 'arxos',
    password: process.env.DATABASE_PASSWORD || 'arxos_dev_2025',
    name: process.env.DATABASE_NAME || 'arxos_fractal',
    logging: process.env.DATABASE_LOGGING === 'true',
    poolSize: parseInt(process.env.DATABASE_POOL_SIZE, 10) || 10,
  },
  
  redis: {
    host: process.env.REDIS_HOST || 'localhost',
    port: parseInt(process.env.REDIS_PORT, 10) || 6380,
    password: process.env.REDIS_PASSWORD || '',
    db: parseInt(process.env.REDIS_DB, 10) || 1,
  },
  
  minio: {
    endpoint: process.env.MINIO_ENDPOINT || 'localhost',
    port: parseInt(process.env.MINIO_PORT, 10) || 9000,
    useSSL: process.env.MINIO_USE_SSL === 'true',
    accessKey: process.env.MINIO_ACCESS_KEY || 'arxos',
    secretKey: process.env.MINIO_SECRET_KEY || 'arxos_minio_2025',
    bucketName: process.env.MINIO_BUCKET || 'arxos-fractal',
  },
  
  cache: {
    ttl: parseInt(process.env.CACHE_TTL, 10) || 300, // 5 minutes
    maxItems: parseInt(process.env.CACHE_MAX_ITEMS, 10) || 1000,
  },
  
  scale: {
    levels: {
      campus: 10.0,
      building: 1.0,
      floor: 0.1,
      room: 0.01,
      fixture: 0.001,
      component: 0.0001,
      schematic: 0.00001,
    },
    detailBudget: {
      min: parseInt(process.env.MIN_DETAIL_BUDGET, 10) || 500,
      max: parseInt(process.env.MAX_DETAIL_BUDGET, 10) || 5000,
      default: parseInt(process.env.DEFAULT_DETAIL_BUDGET, 10) || 1000,
    },
  },
  
  viewport: {
    tileSize: parseInt(process.env.TILE_SIZE, 10) || 256,
    preloadRadius: parseInt(process.env.PRELOAD_RADIUS, 10) || 2,
    maxZoom: parseInt(process.env.MAX_ZOOM, 10) || 22,
    minZoom: parseInt(process.env.MIN_ZOOM, 10) || 0,
  },
  
  performance: {
    targetZoomTime: parseInt(process.env.TARGET_ZOOM_TIME, 10) || 200, // ms
    targetFrameTime: parseInt(process.env.TARGET_FRAME_TIME, 10) || 16, // ms (60fps)
    warnThreshold: parseFloat(process.env.PERF_WARN_THRESHOLD) || 1.5, // 1.5x target
  },
  
  websocket: {
    pingInterval: parseInt(process.env.WS_PING_INTERVAL, 10) || 30000, // 30s
    pingTimeout: parseInt(process.env.WS_PING_TIMEOUT, 10) || 5000, // 5s
  },
  
  cors: {
    origin: process.env.CORS_ORIGIN || '*',
  },
});