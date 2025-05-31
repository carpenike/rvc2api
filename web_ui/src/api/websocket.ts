/**
 * WebSocket Client for Real-time Data
 *
 * This module provides WebSocket connectivity for real-time updates
 * from the backend, including entity updates, CAN messages, and system status.
 */

import { WS_BASE, env, logApiRequest, logApiResponse } from './client';
import type {
  CANMessageUpdate,
  EntityUpdateMessage,
  SystemStatusMessage,
  WebSocketMessage,
  WebSocketMessageType
} from './types';

/**
 * WebSocket connection states
 */
export type WebSocketState = 'connecting' | 'connected' | 'disconnected' | 'error';

/**
 * WebSocket event handlers interface
 */
export interface WebSocketHandlers {
  onOpen?: () => void;
  onClose?: (event: CloseEvent) => void;
  onError?: (error: Event) => void;
  onMessage?: (message: WebSocketMessage) => void;
  onEntityUpdate?: (message: EntityUpdateMessage) => void;
  onCANMessage?: (message: CANMessageUpdate) => void;
  onSystemStatus?: (message: SystemStatusMessage) => void;
}

/**
 * WebSocket client configuration
 */
export interface WebSocketConfig {
  /** Auto-reconnect on connection loss */
  autoReconnect?: boolean;
  /** Reconnection delay in milliseconds */
  reconnectDelay?: number;
  /** Maximum reconnection attempts (0 = infinite) */
  maxReconnectAttempts?: number;
  /** Connection timeout in milliseconds */
  connectionTimeout?: number;
  /** Heartbeat interval in milliseconds (0 = disabled) */
  heartbeatInterval?: number;
}

/**
 * Default WebSocket configuration
 */
const defaultConfig: Required<WebSocketConfig> = {
  autoReconnect: true,
  reconnectDelay: 3000,
  maxReconnectAttempts: 0, // Infinite
  connectionTimeout: 10000,
  heartbeatInterval: 30000, // 30 seconds
};

/**
 * WebSocket client class for managing real-time connections
 */
export class RVCWebSocketClient {
  private socket: WebSocket | null = null;
  private handlers: WebSocketHandlers = {};
  private config: Required<WebSocketConfig>;
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private connectionTimer: NodeJS.Timeout | null = null;
  private _state: WebSocketState = 'disconnected';

  constructor(
    private endpoint: string,
    handlers: WebSocketHandlers = {},
    config: WebSocketConfig = {}
  ) {
    this.handlers = handlers;
    this.config = { ...defaultConfig, ...config };
  }

  /**
   * Get current connection state
   */
  get state(): WebSocketState {
    return this._state;
  }

  /**
   * Get current connection status
   */
  get isConnected(): boolean {
    return this._state === 'connected' && this.socket?.readyState === WebSocket.OPEN;
  }

  /**
   * Connect to the WebSocket endpoint
   */
  connect(): void {
    if (this.socket?.readyState === WebSocket.CONNECTING || this.isConnected) {
      return;
    }

    this.cleanup();
    this._state = 'connecting';

    const wsUrl = `${WS_BASE}${this.endpoint}`;

    if (env.isDevelopment) {
      logApiRequest('WS CONNECT', wsUrl);
    }

    this.socket = new WebSocket(wsUrl);
    this.setupEventHandlers();
    this.setupConnectionTimeout();
  }

  /**
   * Disconnect from the WebSocket
   */
  disconnect(): void {
    this.config.autoReconnect = false; // Prevent automatic reconnection
    this.cleanup();
    this._state = 'disconnected';
  }

  /**
   * Send a message through the WebSocket
   *
   * @param message - Message to send
   */
  send(message: unknown): void {
    if (!this.isConnected) {
      throw new Error('WebSocket is not connected');
    }

    const messageStr = typeof message === 'string' ? message : JSON.stringify(message);
    this.socket!.send(messageStr);

    if (env.isDevelopment) {
      logApiRequest('WS SEND', this.endpoint, message);
    }
  }

  /**
   * Update event handlers
   */
  setHandlers(handlers: WebSocketHandlers): void {
    this.handlers = { ...this.handlers, ...handlers };
  }

  /**
   * Update configuration
   */
  updateConfig(config: Partial<WebSocketConfig>): void {
    this.config = { ...this.config, ...config };
  }

  /**
   * Setup WebSocket event handlers
   */
  private setupEventHandlers(): void {
    if (!this.socket) return;

    this.socket.onopen = () => {
      this.clearConnectionTimeout();
      this._state = 'connected';
      this.reconnectAttempts = 0;

      if (env.isDevelopment) {
        logApiResponse(`WS CONNECTED`, this.endpoint);
      }

      this.setupHeartbeat();
      this.handlers.onOpen?.();
    };

    this.socket.onclose = (event) => {
      this.cleanup();
      this._state = 'disconnected';

      if (env.isDevelopment) {
        console.log(`🔌 WebSocket closed: ${this.endpoint}`, { code: event.code, reason: event.reason });
      }

      this.handlers.onClose?.(event);

      if (this.config.autoReconnect && this.shouldReconnect()) {
        this.scheduleReconnect();
      }
    };

    this.socket.onerror = (event) => {
      this._state = 'error';

      if (env.isDevelopment) {
        console.error(`❌ WebSocket error: ${this.endpoint}`, event);
      }

      this.handlers.onError?.(event);
    };

    this.socket.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);

        if (env.isDevelopment) {
          logApiResponse(`WS MESSAGE ${this.endpoint}`, message);
        }

        // Call generic message handler
        this.handlers.onMessage?.(message);

        // Call specific handlers based on message type
        this.handleTypedMessage(message as WebSocketMessageType);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error, event.data);
      }
    };
  }

  /**
   * Handle typed WebSocket messages
   */
  private handleTypedMessage(message: WebSocketMessageType): void {
    switch (message.type) {
      case 'entity_update':
        this.handlers.onEntityUpdate?.(message as EntityUpdateMessage);
        break;
      case 'can_message':
        this.handlers.onCANMessage?.(message as CANMessageUpdate);
        break;
      case 'system_status':
        this.handlers.onSystemStatus?.(message as SystemStatusMessage);
        break;
      default:
        // Handle unknown message types gracefully
        if (env.isDevelopment) {
          console.log('Unknown WebSocket message type:', message.type, message);
        }
    }
  }

  /**
   * Setup connection timeout
   */
  private setupConnectionTimeout(): void {
    this.connectionTimer = setTimeout(() => {
      if (this._state === 'connecting') {
        this.socket?.close();
        this._state = 'error';
        console.error(`WebSocket connection timeout: ${this.endpoint}`);
      }
    }, this.config.connectionTimeout);
  }

  /**
   * Clear connection timeout
   */
  private clearConnectionTimeout(): void {
    if (this.connectionTimer) {
      clearTimeout(this.connectionTimer);
      this.connectionTimer = null;
    }
  }

  /**
   * Setup heartbeat to keep connection alive
   */
  private setupHeartbeat(): void {
    if (this.config.heartbeatInterval <= 0) return;

    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected) {
        try {
          this.send({ type: 'ping', timestamp: new Date().toISOString() });
        } catch (error) {
          console.warn('Failed to send heartbeat:', error);
        }
      }
    }, this.config.heartbeatInterval);
  }

  /**
   * Determine if we should attempt to reconnect
   */
  private shouldReconnect(): boolean {
    return this.config.maxReconnectAttempts === 0 ||
           this.reconnectAttempts < this.config.maxReconnectAttempts;
  }

  /**
   * Schedule a reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    this.reconnectAttempts++;

    if (env.isDevelopment) {
      console.log(`📡 Scheduling WebSocket reconnect attempt ${this.reconnectAttempts} in ${this.config.reconnectDelay}ms`);
    }

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, this.config.reconnectDelay);
  }

  /**
   * Cleanup timers and connections
   */
  private cleanup(): void {
    this.clearConnectionTimeout();

    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.socket) {
      this.socket.onopen = null;
      this.socket.onclose = null;
      this.socket.onerror = null;
      this.socket.onmessage = null;

      if (this.socket.readyState === WebSocket.OPEN) {
        this.socket.close();
      }

      this.socket = null;
    }
  }
}

//
// ===== CONVENIENCE FUNCTIONS =====
//

/**
 * Create a WebSocket client for entity updates
 *
 * @param handlers - Event handlers
 * @param config - Optional configuration
 * @returns WebSocket client instance
 */
export function createEntityWebSocket(
  handlers: WebSocketHandlers = {},
  config: WebSocketConfig = {}
): RVCWebSocketClient {
  return new RVCWebSocketClient('/entities', handlers, config);
}

/**
 * Create a WebSocket client for CAN message scanning
 *
 * @param handlers - Event handlers
 * @param config - Optional configuration
 * @returns WebSocket client instance
 */
export function createCANScanWebSocket(
  handlers: WebSocketHandlers = {},
  config: WebSocketConfig = {}
): RVCWebSocketClient {
  return new RVCWebSocketClient('/can/scan', handlers, config);
}

/**
 * Create a WebSocket client for system status updates
 *
 * @param handlers - Event handlers
 * @param config - Optional configuration
 * @returns WebSocket client instance
 */
export function createSystemStatusWebSocket(
  handlers: WebSocketHandlers = {},
  config: WebSocketConfig = {}
): RVCWebSocketClient {
  return new RVCWebSocketClient('/system/status', handlers, config);
}

//
// ===== UTILITY FUNCTIONS =====
//

/**
 * Check if WebSocket is supported in the current environment
 *
 * @returns True if WebSocket is available
 */
export function isWebSocketSupported(): boolean {
  return typeof WebSocket !== 'undefined';
}

/**
 * Get WebSocket ready state as human-readable string
 *
 * @param readyState - WebSocket ready state number
 * @returns Human-readable state string
 */
export function getWebSocketStateString(readyState: number): string {
  switch (readyState) {
    case WebSocket.CONNECTING:
      return 'connecting';
    case WebSocket.OPEN:
      return 'open';
    case WebSocket.CLOSING:
      return 'closing';
    case WebSocket.CLOSED:
      return 'closed';
    default:
      return 'unknown';
  }
}
