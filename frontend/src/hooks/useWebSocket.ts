// frontend/src/hooks/useWebSocket.ts
import { useEffect, useState, useCallback } from "react";
import { useWebSocketContext } from "../providers/WebSocketProvider";

export function useWebSocket<T = any>() {
  const ctx = useWebSocketContext();
  const webSocketService = ctx?.webSocketService;

  if (!webSocketService) {
    throw new Error("WebSocketService is not initialized");
  }

  const [data, setData] = useState<T | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(webSocketService.isConnected());
  const [error, setError] = useState<Error | null>(null);

  const send = useCallback((msg: any) => {
    try {
      webSocketService.send(msg);
    } catch (err) {
      setError(err as Error);
    }
  }, [webSocketService]);

  useEffect(() => {
    const handleConnectionChange = (connected: boolean) => setIsConnected(connected);
    const handleMessage = (message: T) => setData(message);

    webSocketService.onConnectionChange(handleConnectionChange);
    webSocketService.onMessage(handleMessage);

    return () => {
      webSocketService.offConnectionChange(handleConnectionChange);
      webSocketService.offMessage(handleMessage as any);
    };
  }, [webSocketService]);

  return { data, isConnected, error, send };
}
