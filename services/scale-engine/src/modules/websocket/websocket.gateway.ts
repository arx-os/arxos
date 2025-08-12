import {
  WebSocketGateway as WSGateway,
  WebSocketServer,
  SubscribeMessage,
  OnGatewayInit,
  OnGatewayConnection,
  OnGatewayDisconnect,
  MessageBody,
  ConnectedSocket,
} from '@nestjs/websockets';
import { Logger } from '@nestjs/common';
import { Server, Socket } from 'socket.io';

@WSGateway({
  cors: {
    origin: '*',
  },
  namespace: '/fractal',
})
export class WebSocketGateway
  implements OnGatewayInit, OnGatewayConnection, OnGatewayDisconnect
{
  @WebSocketServer()
  server: Server;

  private logger: Logger = new Logger('WebSocketGateway');
  private connectedClients: Map<string, Socket> = new Map();

  afterInit(server: Server) {
    this.logger.log('WebSocket Gateway initialized');
  }

  handleConnection(client: Socket) {
    this.logger.log(`Client connected: ${client.id}`);
    this.connectedClients.set(client.id, client);
    
    // Send initial connection message
    client.emit('connected', {
      message: 'Connected to Fractal ArxObject WebSocket',
      clientId: client.id,
    });
  }

  handleDisconnect(client: Socket) {
    this.logger.log(`Client disconnected: ${client.id}`);
    this.connectedClients.delete(client.id);
  }

  @SubscribeMessage('subscribe-viewport')
  handleSubscribeViewport(
    @MessageBody() data: { viewportId: string },
    @ConnectedSocket() client: Socket,
  ): void {
    client.join(`viewport:${data.viewportId}`);
    client.emit('subscribed', {
      channel: `viewport:${data.viewportId}`,
    });
  }

  @SubscribeMessage('unsubscribe-viewport')
  handleUnsubscribeViewport(
    @MessageBody() data: { viewportId: string },
    @ConnectedSocket() client: Socket,
  ): void {
    client.leave(`viewport:${data.viewportId}`);
    client.emit('unsubscribed', {
      channel: `viewport:${data.viewportId}`,
    });
  }

  // Emit viewport updates to subscribed clients
  emitViewportUpdate(viewportId: string, data: any): void {
    this.server.to(`viewport:${viewportId}`).emit('viewport-update', data);
  }

  // Emit object updates
  emitObjectUpdate(objectId: string, data: any): void {
    this.server.emit('object-update', {
      objectId,
      ...data,
    });
  }

  // Broadcast performance metrics
  broadcastMetrics(metrics: any): void {
    this.server.emit('metrics', metrics);
  }

  getConnectedClientsCount(): number {
    return this.connectedClients.size;
  }
}