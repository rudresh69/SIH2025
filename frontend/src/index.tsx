// frontend/src/index.tsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

// Updated WebSocket + Redux Provider
import { WebSocketStoreProvider } from "./providers/WebSocketProvider";

// Replace this with your actual backend WebSocket URL
const WEBSOCKET_URL = "ws://localhost:8000/ws/live";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <WebSocketStoreProvider initialUrl={WEBSOCKET_URL}>
      <App />
    </WebSocketStoreProvider>
  </React.StrictMode>
);
