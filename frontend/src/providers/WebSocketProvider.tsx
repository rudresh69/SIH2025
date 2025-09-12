// frontend/src/providers/WebSocketProvider.tsx
import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from "react";
import { WebSocketService } from '../services/WebSocketService'; // --- CHANGE: Import the singleton service

// ---------------------- WebSocket Context ----------------------
type WebSocketContextType = {
  webSocketService: WebSocketService | null;
  setUrl: (url: string) => void;
};

export const WebSocketContext = createContext<WebSocketContextType | undefined>(
  undefined
);

export const useWebSocketContext = (): WebSocketContextType => {
  const ctx = useContext(WebSocketContext);
  if (!ctx)
    throw new Error(
      "useWebSocketContext must be used within a WebSocketProvider"
    );
  return ctx;
};

// ---------------------- Combined Provider ----------------------
type WebSocketProviderProps = {
  initialUrl?: string;
  children: ReactNode;
};

export const WebSocketStoreProvider: React.FC<WebSocketProviderProps> = ({
  initialUrl,
  children,
}) => {
  // --- CHANGE: Use the singleton instance
  const [wsService] = useState(() => WebSocketService.getInstance(initialUrl || ""));
  const [url, setUrlState] = useState(initialUrl || "");

  const setUrl = (newUrl: string) => {
    if (url !== newUrl) {
      setUrlState(newUrl);
      wsService.changeUrl(newUrl);
    }
  };

  return (
    <WebSocketContext.Provider value={{ webSocketService: wsService, setUrl }}>
      {children}
    </WebSocketContext.Provider>
  );
};