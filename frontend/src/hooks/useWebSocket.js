import { useState, useEffect, useRef, useCallback } from 'react';

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export const useWebSocket = (endpoint = '/ws/compliance', onMessageCallback) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const connect = useCallback(() => {
    try {
      const url = `${WS_BASE_URL}${endpoint}`;
      const socket = new WebSocket(url);
      wsRef.current = socket;

      socket.onopen = () => {
        setIsConnected(true);
      };

      socket.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);
          setLastMessage(parsed);
          if (onMessageCallback) {
            onMessageCallback(parsed);
          }
        } catch (e) {
          // Keep-alive or non-JSON message
        }
      };

      socket.onclose = () => {
        setIsConnected(false);
        // Automatic reconnect after 5 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 5000);
      };

      socket.onerror = () => {
        socket.close();
      };
    } catch (err) {
      setIsConnected(false);
    }
  }, [endpoint, onMessageCallback]);

  useEffect(() => {
    connect();

    // Heartbeat ping every 25 seconds
    const pingInterval = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send('ping');
      }
    }, 25000);

    return () => {
      clearInterval(pingInterval);
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return { isConnected, lastMessage };
};
