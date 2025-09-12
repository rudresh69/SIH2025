# WebSocket Integration Documentation

## Overview

This document describes the WebSocket integration between the React frontend and FastAPI backend for the Rockfall Prediction System. The WebSocket connection enables real-time data flow from sensors and ML models to the frontend UI components.

## Architecture

### Backend (FastAPI)

- WebSocket endpoint: `/ws/live`
- Provides real-time sensor data, rockfall predictions, and weather forecasts
- Combines data from multiple sources into a single WebSocket stream

### Frontend (React)

- Uses a singleton WebSocketService for connection management
- Provides a WebSocketProvider context for application-wide access
- Custom useWebSocket hook for React components

## Implementation Details

### WebSocketService

The `WebSocketService` class manages the WebSocket connection, handles reconnection logic, and distributes messages to subscribers.

```typescript
// src/services/WebSocketService.ts
export class WebSocketService {
  // Singleton instance management
  private static instance: WebSocketService;
  
  public static getInstance(url?: string): WebSocketService {
    // Returns existing instance or creates a new one
  }
  
  // Connection management
  public connect(): void { /* ... */ }
  public disconnect(): void { /* ... */ }
  public isConnected(): boolean { /* ... */ }
  
  // Message handling
  public send(data: any): void { /* ... */ }
  public onMessage<T>(callback: (data: T) => void): void { /* ... */ }
  public offMessage(callback: (data: any) => void): void { /* ... */ }
  
  // Connection status
  public onConnectionChange(callback: (connected: boolean) => void): void { /* ... */ }
  public offConnectionChange(callback: (connected: boolean) => void): void { /* ... */ }
}
```

### WebSocketProvider

The `WebSocketProvider` component provides the WebSocket connection to all child components through React Context.

```typescript
// src/providers/WebSocketProvider.tsx
export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children, url }) => {
  const webSocketService = WebSocketService.getInstance(url);
  return (
    <WebSocketContext.Provider value={{ webSocketService }}>
      {children}
    </WebSocketContext.Provider>
  );
};
```

### useWebSocket Hook

The `useWebSocket` hook provides a simple interface for components to access WebSocket data and connection status.

```typescript
// src/hooks/useWebSocket.ts
export function useWebSocket<T>() {
  const [data, setData] = useState<T | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const { webSocketService } = useWebSocketContext();
  
  // Subscribe to WebSocket messages and connection status
  useEffect(() => { /* ... */ }, [webSocketService]);
  
  return { data, isConnected };
}
```

## Data Flow

1. Backend collects sensor data and generates predictions
2. Data is sent through WebSocket to connected clients
3. WebSocketService receives and parses the data
4. Components using useWebSocket hook receive updated data
5. UI components re-render with the latest data

## Data Structures

### Sensor Readings

```typescript
interface SensorReadings {
  timestamp: string;
  accelerometer: number;
  geophone: number;
  seismometer: number;
  crack_sensor: number;
  inclinometer: number;
  extensometer: number;
  moisture_sensor: number;
  piezometer: number;
  rain_sensor_mmhr: number;
  temperature_celsius: number;
  humidity_percent: number;
  prediction: number;
  event_active: boolean;
  event_phase: string;
}
```

### Weather Forecast

```typescript
interface WeatherForecastResponse {
  timestamp: string;
  forecast: {
    temperature_celsius: number[];
    humidity_percent: number[];
    rain_sensor_mmhr: number[];
  };
}
```

## Usage Examples

### Basic Component Integration

```tsx
import { useWebSocket } from '../hooks/useWebSocket';

interface MyData {
  value: number;
  // other fields...
}

const MyComponent: React.FC = () => {
  const { data, isConnected } = useWebSocket<MyData>();
  
  return (
    <div>
      <div>Connection status: {isConnected ? 'Connected' : 'Disconnected'}</div>
      {data && <div>Value: {data.value}</div>}
    </div>
  );
};
```

## Troubleshooting

### Connection Issues

- Ensure the backend server is running
- Check that the WebSocket URL is correct in the WebSocketProvider
- Verify that CORS is properly configured on the backend
- Check browser console for WebSocket errors

### Data Not Updating

- Verify that components are using the useWebSocket hook correctly
- Check that the data structure matches what the backend is sending
- Ensure the WebSocketProvider is wrapping the application

## Future Improvements

- Add authentication for WebSocket connections
- Implement message queuing for offline support
- Add support for binary data transfer for efficiency
- Implement selective subscriptions to specific data types