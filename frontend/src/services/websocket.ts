/**
 * WebSocket Service
 * Handles real-time communication with backend
 */

import type {
  WebSocketMessage,
  BiometricToken,
  KnowledgePayload,
  UIComponentTree,
  FaceLandmark,
} from '@/types';

type MessageHandler = (message: WebSocketMessage) => void;
type ConnectionHandler = (connected: boolean) => void;
type ErrorHandler = (error: Error) => void;

interface WebSocketServiceConfig {
  url: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
}

export class WebSocketService {
  private ws: WebSocket | null = null;
  private config: Required<WebSocketServiceConfig>;
  private reconnectAttempts = 0;
  private reconnectTimeout: number | null = null;
  private heartbeatInterval: number | null = null;
  private messageHandlers: Set<MessageHandler> = new Set();
  private connectionHandlers: Set<ConnectionHandler> = new Set();
  private errorHandlers: Set<ErrorHandler> = new Set();
  private isIntentionallyClosed = false;

  constructor(config: WebSocketServiceConfig) {
    this.config = {
      url: config.url,
      reconnectInterval: config.reconnectInterval || 3000,
      maxReconnectAttempts: config.maxReconnectAttempts || 5,
      heartbeatInterval: config.heartbeatInterval || 30000,
    };
  }

  /**
   * Connect to WebSocket server
   */
  connect(sessionId: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.warn('WebSocket already connected');
      return;
    }

    this.isIntentionallyClosed = false;
    const wsUrl = `${this.config.url}/${sessionId}`;

    try {
      this.ws = new WebSocket(wsUrl);
      this.setupEventHandlers();
    } catch (error) {
      this.handleError(error instanceof Error ? error : new Error('Failed to connect'));
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.isIntentionallyClosed = true;
    this.clearReconnectTimeout();
    this.clearHeartbeat();

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.notifyConnectionHandlers(false);
  }

  /**
   * Send biometric analysis request
   */
  sendBiometricData(sessionId: string, landmarks: FaceLandmark[][], frameCount: number): void {
    this.send({
      type: 'biometric_analysis',
      data: {
        session_id: sessionId,
        landmarks: landmarks,
        frame_count: frameCount,
        capture_duration: frameCount / 30, // Assuming 30 FPS
        timestamp: new Date().toISOString(),
      },
    });
  }

  /**
   * Send knowledge query
   */
  sendKnowledgeQuery(sessionId: string, query: string, biometricToken?: BiometricToken): void {
    this.send({
      type: 'knowledge_query',
      data: {
        session_id: sessionId,
        query: query,
        biometric_token: biometricToken,
        timestamp: new Date().toISOString(),
      },
    });
  }

  /**
   * Send full pipeline request (biometric + knowledge + UI)
   */
  sendFullPipeline(
    sessionId: string,
    query: string,
    landmarks: FaceLandmark[][],
    frameCount: number
  ): void {
    this.send({
      type: 'full_pipeline',
      data: {
        session_id: sessionId,
        query: query,
        landmarks: landmarks,
        frame_count: frameCount,
        capture_duration: frameCount / 30,
        timestamp: new Date().toISOString(),
      },
    });
  }

  /**
   * Send engagement signal
   */
  sendEngagementSignal(action: 'understood' | 'confused' | 'need_more' | 'complete'): void {
    this.send({
      type: 'engagement_signal',
      data: { action },
    });
  }

  /**
   * Send ping to keep connection alive
   */
  sendPing(): void {
    this.send({
      type: 'ping',
      data: { timestamp: new Date().toISOString() },
    });
  }

  /**
   * Register message handler
   */
  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler);
    return () => this.messageHandlers.delete(handler);
  }

  /**
   * Register connection handler
   */
  onConnection(handler: ConnectionHandler): () => void {
    this.connectionHandlers.add(handler);
    return () => this.connectionHandlers.delete(handler);
  }

  /**
   * Register error handler
   */
  onError(handler: ErrorHandler): () => void {
    this.errorHandlers.add(handler);
    return () => this.errorHandlers.delete(handler);
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Get connection state
   */
  getReadyState(): number | null {
    return this.ws?.readyState ?? null;
  }

  // Private methods

  private setupEventHandlers(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.notifyConnectionHandlers(true);
      this.startHeartbeat();
    };

    this.ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        this.notifyMessageHandlers(message);

        // Handle pong response
        if (message.type === 'pong') {
          console.debug('Received pong');
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.ws.onerror = (event) => {
      console.error('WebSocket error event:', event);
      // Don't immediately show error to user - wait for onclose to handle reconnection
      // Only show error if connection actually fails (handled in onclose)
    };

    this.ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
      this.clearHeartbeat();
      this.notifyConnectionHandlers(false);

      // Only show error if this was an abnormal closure and we can't reconnect
      if (!this.isIntentionallyClosed) {
        if (event.code !== 1000 && event.code !== 1001) {
          // Abnormal closure - attempt reconnect
          this.attemptReconnect();
        } else {
          // Normal closure - just log it
          console.log('WebSocket closed normally');
        }
      }
    };
  }

  private send(message: WebSocketMessage): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected');
      this.handleError(new Error('WebSocket not connected'));
      return;
    }

    try {
      this.ws.send(JSON.stringify(message));
    } catch (error) {
      console.error('Failed to send WebSocket message:', error);
      this.handleError(error instanceof Error ? error : new Error('Failed to send message'));
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      console.error('Max reconnect attempts reached');
      this.handleError(new Error('Failed to reconnect after maximum attempts'));
      return;
    }

    this.reconnectAttempts++;
    console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.config.maxReconnectAttempts})...`);

    this.reconnectTimeout = setTimeout(() => {
      // Extract session ID from current URL
      const sessionId = this.ws?.url.split('/').pop() || '';
      if (sessionId) {
        this.connect(sessionId);
      }
    }, this.config.reconnectInterval);
  }

  private startHeartbeat(): void {
    this.clearHeartbeat();
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected()) {
        this.sendPing();
      }
    }, this.config.heartbeatInterval);
  }

  private clearHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  private clearReconnectTimeout(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
  }

  private notifyMessageHandlers(message: WebSocketMessage): void {
    this.messageHandlers.forEach((handler) => {
      try {
        handler(message);
      } catch (error) {
        console.error('Error in message handler:', error);
      }
    });
  }

  private notifyConnectionHandlers(connected: boolean): void {
    this.connectionHandlers.forEach((handler) => {
      try {
        handler(connected);
      } catch (error) {
        console.error('Error in connection handler:', error);
      }
    });
  }

  private handleError(error: Error): void {
    this.errorHandlers.forEach((handler) => {
      try {
        handler(error);
      } catch (err) {
        console.error('Error in error handler:', err);
      }
    });
  }
}

// Singleton instance
let wsServiceInstance: WebSocketService | null = null;

/**
 * Get WebSocket service instance
 */
export function getWebSocketService(config?: WebSocketServiceConfig): WebSocketService {
  if (!wsServiceInstance && config) {
    wsServiceInstance = new WebSocketService(config);
  }

  if (!wsServiceInstance) {
    throw new Error('WebSocket service not initialized. Provide config on first call.');
  }

  return wsServiceInstance;
}

/**
 * Reset WebSocket service (useful for testing)
 */
export function resetWebSocketService(): void {
  if (wsServiceInstance) {
    wsServiceInstance.disconnect();
    wsServiceInstance = null;
  }
}

// Made with Bob for IBM AI Builders Challenge