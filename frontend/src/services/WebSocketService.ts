// frontend/src/services/WebSocketService.ts
type MessageCallback = (data: any) => void;
type ConnectionCallback = (connected: boolean) => void;

export class WebSocketService {
  private static instance: WebSocketService | null = null;
  private socket: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectInterval = 2000;

  private messageCallbacks: MessageCallback[] = [];
  private connectionCallbacks: ConnectionCallback[] = [];

  private constructor(url: string) {
    this.url = url;
    this.connect();
  }

  // Singleton getter
  public static getInstance(url?: string): WebSocketService {
    if (!WebSocketService.instance) {
      if (!url) throw new Error("WebSocket URL must be provided for the first instance");
      WebSocketService.instance = new WebSocketService(url);
    } else if (url && WebSocketService.instance.url !== url) {
      // If URL changes, reconnect
      WebSocketService.instance.changeUrl(url);
    }
    return WebSocketService.instance;
  }

  private connect() {
    try {
      this.socket = new WebSocket(this.url);
    } catch (err) {
      console.error("WebSocket connection failed immediately", err);
      this.scheduleReconnect();
      return;
    }

    this.socket.onopen = () => {
      this.reconnectAttempts = 0;
      this.connectionCallbacks.forEach(cb => cb(true));
      console.log(`⚡ WebSocket connected to ${this.url}`);
    };

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.messageCallbacks.forEach(cb => cb(data));
      } catch (err) {
        console.error("❌ WebSocket message parse error", err);
      }
    };

    this.socket.onerror = () => {
      // Don't spam console; handled in onclose
    };

    this.socket.onclose = () => {
      this.connectionCallbacks.forEach(cb => cb(false));
      console.warn(`⚠️ WebSocket disconnected. Reconnecting... (${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);
      this.scheduleReconnect();
    };
  }

private scheduleReconnect() {
  this.reconnectAttempts++;
  if (this.reconnectAttempts <= this.maxReconnectAttempts) {
    setTimeout(() => this.connect(), 2000);
  } else {
    console.error("❌ Max WebSocket reconnect attempts reached");
  }
}


  // Change URL dynamically
  public changeUrl(newUrl: string) {
    if (this.url === newUrl) return;
    console.log("🔄 Changing WebSocket URL to:", newUrl);
    this.url = newUrl;
    this.socket?.close();
  }

  public send(msg: any) {
    if (this.isConnected()) {
      this.socket!.send(JSON.stringify(msg));
    } else {
      console.warn("⚠️ WebSocket not connected. Message not sent:", msg);
    }
  }

  public onMessage(cb: MessageCallback) {
    this.messageCallbacks.push(cb);
  }

  public offMessage(cb: MessageCallback) {
    this.messageCallbacks = this.messageCallbacks.filter(c => c !== cb);
  }

  public onConnectionChange(cb: ConnectionCallback) {
    this.connectionCallbacks.push(cb);
  }

  public offConnectionChange(cb: ConnectionCallback) {
    this.connectionCallbacks = this.connectionCallbacks.filter(c => c !== cb);
  }

  public isConnected(): boolean {
    return this.socket?.readyState === WebSocket.OPEN;
  }
}
