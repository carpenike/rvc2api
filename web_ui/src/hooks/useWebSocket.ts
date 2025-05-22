import { useCallback, useEffect, useRef, useState } from "react";
import { getWebSocketUrl } from "../utils/config";

/** Status of the WebSocket connection */
type WebSocketStatus = "connecting" | "open" | "closed" | "error";

/**
 * Options for configuring the WebSocket hook
 */
interface UseWebSocketOptions {
  /** Callback for when a message is received */
  onMessage?: (data: unknown) => void;

  /** Milliseconds to wait before attempting reconnection (default: 2000) */
  reconnectInterval?: number;

  /** Maximum number of reconnection attempts (default: 10) */
  reconnectAttempts?: number;

  /** Callback for when the socket connection is established */
  onOpen?: () => void;

  /** Callback for when the socket connection is closed */
  onClose?: () => void;

  /** Callback for when a socket error occurs */
  onError?: (error: Event) => void;
}

/**
 * A custom React hook for managing WebSocket connections with automatic reconnection
 *
 * Provides real-time communication capabilities with error handling, auto-reconnect,
 * and proper cleanup on unmount
 *
 * @param path - The WebSocket endpoint path (e.g., "/ws/entities")
 * @param options - Configuration options for the WebSocket
 *   @param options.onMessage Callback for message events
 *   @param options.reconnectInterval Reconnect interval in ms
 *   @param options.reconnectAttempts Number of reconnect attempts
 *   @param options.onOpen Callback for open event
 *   @param options.onClose Callback for close event
 *   @param options.onError Callback for error event
 * @returns Object containing connection status, received messages, and a function to send messages
 *
 * @example
 * ```tsx
 * const { status, messages, sendMessage } = useWebSocket("/ws/entities", {
 *   onMessage: (data) => console.log("Received:", data),
 *   reconnectInterval: 3000
 * });
 * ```
 */
export function useWebSocket<T = unknown>(
  path: string,
  {
    onMessage,
    reconnectInterval = 2000,
    reconnectAttempts = 10,
    onOpen,
    onClose,
    onError
  }: UseWebSocketOptions = {}
) {
  const [status, setStatus] = useState<WebSocketStatus>("connecting");
  const [messages, setMessages] = useState<T[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCount = useRef(0);
  const shouldReconnect = useRef(true);

  const connect = useCallback(() => {
    const url = getWebSocketUrl(path);
    setStatus("connecting");
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus("open");
      reconnectCount.current = 0;
      onOpen?.();
    };

    ws.onmessage = (event) => {
      let data: T | undefined;
      try {
        data = JSON.parse(event.data);
      } catch {
        // fallback to raw data if not JSON
        data = event.data as T;
      }
      setMessages((prev) => [...prev, data as T]);
      onMessage?.(data);
    };

    ws.onclose = () => {
      setStatus("closed");
      onClose?.();
      if (shouldReconnect.current && reconnectCount.current < reconnectAttempts) {
        reconnectCount.current += 1;
        setTimeout(connect, reconnectInterval);
      }
    };

    ws.onerror = (event) => {
      setStatus("error");
      onError?.(event);
      ws.close();
    };
  }, [path, reconnectInterval, reconnectAttempts, onMessage, onOpen, onClose, onError]);

  useEffect(() => {
    shouldReconnect.current = true;
    connect();
    return () => {
      shouldReconnect.current = false;
      wsRef.current?.close();
    };
  }, [connect]);

  const sendMessage = useCallback((msg: unknown) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        typeof msg === "string" ? msg : JSON.stringify(msg)
      );
    }
  }, []);

  return {
    status,
    messages,
    sendMessage,
    /**
     * The current WebSocket instance (read-only, for advanced use)
     */
    socket: wsRef.current
  };
}
