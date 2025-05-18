import { useCallback, useEffect, useRef, useState } from "react";

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
 * @param url - The WebSocket endpoint URL
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
 * const { status, messages, sendMessage } = useWebSocket("ws://localhost:8000/ws", {
 *   onMessage: (data) => console.log("Received:", data),
 *   reconnectInterval: 3000
 * });
 * ```
 */
export function useWebSocket(
  url: string,
  {
    onMessage,
    reconnectInterval = 2000,
    reconnectAttempts = 10,
    onOpen,
    onClose,
    onError
  }: UseWebSocketOptions = {}
) {
  /**
   * Custom React hook for managing a WebSocket connection.
   * @param url The WebSocket URL
   * @param options.onMessage Callback for message events
   * @param options.reconnectInterval Reconnect interval in ms
   * @param options.reconnectAttempts Number of reconnect attempts
   * @param options.onOpen Callback for open event
   * @param options.onClose Callback for close event
   * @param options.onError Callback for error event
   */
  const [status, setStatus] = useState<WebSocketStatus>("connecting");
  const [messages, setMessages] = useState<unknown[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const attemptRef = useRef(0);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      // Convert HTTP URL to WebSocket URL if needed
      const wsUrl = url.startsWith("ws")
        ? url
        : url.replace(/^http/, "ws").replace(/^https/, "wss");

      const fullUrl = new URL(wsUrl, window.location.href).href;
      console.log("Connecting to WebSocket at:", fullUrl);
      const ws = new WebSocket(fullUrl);

      ws.onopen = () => {
        console.log("WebSocket connection established");
        setStatus("open");
        attemptRef.current = 0;
        if (onOpen) onOpen();
      };

      ws.onclose = () => {
        console.log("WebSocket connection closed");
        setStatus("closed");
        if (onClose) onClose();

        // Try to reconnect if we haven't exceeded our attempts
        if (attemptRef.current < reconnectAttempts) {
          attemptRef.current += 1;
          reconnectTimeoutRef.current = window.setTimeout(() => {
            console.log(
              `Attempting to reconnect (${attemptRef.current}/${reconnectAttempts})`
            );
            connect();
          }, reconnectInterval);
        }
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        setStatus("error");
        if (onError) onError(error);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setMessages((prev) => [...prev, data]);
          if (onMessage) onMessage(data);
        } catch (error) {
          console.error("Error parsing WebSocket message:", error);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error("Error creating WebSocket:", error);
      setStatus("error");
    }
  }, [
    url,
    reconnectAttempts,
    reconnectInterval,
    onOpen,
    onClose,
    onError,
    onMessage
  ]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  const sendMessage = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
      return true;
    }
    return false;
  }, []);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    status,
    messages,
    sendMessage,
    disconnect,
    reconnect: connect
  };
}
