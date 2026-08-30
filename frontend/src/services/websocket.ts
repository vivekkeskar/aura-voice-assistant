import { WSMessage } from '../types';

export class VoiceWebSocketClient {
  private socket: WebSocket | null = null;
  private url: string;
  private onMessageCallback: (msg: WSMessage) => void;
  private onStatusCallback: (connected: boolean) => void;
  private reconnectInterval: number = 2000;
  private isIntentionalClose: boolean = false;

  constructor(
    url: string,
    onMessage: (msg: WSMessage) => void,
    onStatus: (connected: boolean) => void
  ) {
    this.url = url;
    this.onMessageCallback = onMessage;
    this.onStatusCallback = onStatus;
  }

  public connect() {
    this.isIntentionalClose = false;
    try {
      this.socket = new WebSocket(this.url);

      this.socket.onopen = () => {
        this.onStatusCallback(true);
      };

      this.socket.onmessage = (event) => {
        try {
          const message: WSMessage = JSON.parse(event.data);
          this.onMessageCallback(message);
        } catch (e) {
          console.error("Failed to parse WS JSON message", e);
        }
      };

      this.socket.onerror = (err) => {
        console.error("WebSocket connection error:", err);
      };

      this.socket.onclose = () => {
        this.onStatusCallback(false);
        if (!this.isIntentionalClose) {
          setTimeout(() => this.connect(), this.reconnectInterval);
        }
      };
    } catch (e) {
      console.error("WebSocket setup error:", e);
      this.onStatusCallback(false);
    }
  }

  public send(data: any) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(typeof data === 'string' ? data : JSON.stringify(data));
    }
  }

  public sendInterrupt() {
    this.send({ type: 'interrupt' });
  }

  public sendText(text: string) {
    this.send({ type: 'text_input', text });
  }

  public disconnect() {
    this.isIntentionalClose = true;
    if (this.socket) {
      this.socket.close();
    }
  }
}
