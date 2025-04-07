// WebSocket service for real-time updates
import { Alarm } from '../types/index';
import { displayShutdownScreen } from '../utils/shutdownUtils';

// Get WebSocket URL from environment or default to localhost
const WS_URL = import.meta.env.VITE_WS_URL || 
    (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + 
    window.location.hostname + 
    ':8000/ws';

// Define message types
type WebSocketMessage = {
    type: string;
    data: any;
};

// Define callback types
type AlarmStatusCallback = (isPlaying: boolean) => void;
type WhiteNoiseStatusCallback = (isPlaying: boolean) => void;
type VolumeUpdateCallback = (volume: number) => void;
type ScheduleUpdateCallback = (schedule: string) => void;
type GlobalStatusUpdateCallback = (isOn: boolean) => void;
type AlarmUpdateCallback = (alarms: Alarm[]) => void;
type ShutdownCallback = () => void;
type ConnectionStatusCallback = (isConnected: boolean) => void;

class WebSocketService {
    private socket: WebSocket | null = null;
    private reconnectTimer: number | null = null;
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectDelay = 3000; // 3 seconds
    private isConnected = false;
    
    // Callback registrations
    private alarmStatusCallbacks: AlarmStatusCallback[] = [];
    private whiteNoiseStatusCallbacks: WhiteNoiseStatusCallback[] = [];
    private volumeUpdateCallbacks: VolumeUpdateCallback[] = [];
    private scheduleUpdateCallbacks: ScheduleUpdateCallback[] = [];
    private globalStatusUpdateCallbacks: GlobalStatusUpdateCallback[] = [];
    private alarmUpdateCallbacks: AlarmUpdateCallback[] = [];
    private shutdownCallbacks: ShutdownCallback[] = [];
    private connectionStatusCallbacks: ConnectionStatusCallback[] = [];
    
    constructor() {
        // Initialize connection when service is created
        this.connect();
        
        // Add event listener for when the page is about to unload
        window.addEventListener('beforeunload', () => {
            this.disconnect();
        });
    }
    
    /**
     * Connect to the WebSocket server
     */
    public connect(): void {
        if (this.socket) {
            return; // Already connected or connecting
        }
        
        try {
            this.socket = new WebSocket(WS_URL);
            
            this.socket.onopen = () => {
                console.log('WebSocket connected');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.notifyConnectionStatus(true);
            };
            
            this.socket.onmessage = (event) => {
                this.handleMessage(event);
            };
            
            this.socket.onclose = () => {
                console.log('WebSocket disconnected');
                this.isConnected = false;
                this.socket = null;
                this.notifyConnectionStatus(false);
                this.attemptReconnect();
            };
            
            this.socket.onerror = (error) => {
                console.error('WebSocket error:', error);
                // The onclose handler will be called after this
            };
        } catch (error) {
            console.error('Failed to connect to WebSocket:', error);
            this.attemptReconnect();
        }
    }
    
    /**
     * Disconnect from the WebSocket server
     */
    public disconnect(): void {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
        
        if (this.reconnectTimer) {
            window.clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
    }
    
    /**
     * Attempt to reconnect to the WebSocket server
     */
    private attemptReconnect(): void {
        if (this.reconnectTimer) {
            window.clearTimeout(this.reconnectTimer);
        }
        
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Maximum reconnect attempts reached');
            return;
        }
        
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts - 1);
        console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        
        this.reconnectTimer = window.setTimeout(() => {
            this.connect();
        }, delay);
    }
    
    /**
     * Handle incoming WebSocket messages
     */
    private handleMessage(event: MessageEvent): void {
        try {
            const message: WebSocketMessage = JSON.parse(event.data);
            
            switch (message.type) {
                case 'alarm_status':
                    this.notifyAlarmStatus(message.data.is_playing);
                    break;
                case 'white_noise_status':
                    this.notifyWhiteNoiseStatus(message.data.is_playing);
                    break;
                case 'volume_update':
                    this.notifyVolumeUpdate(message.data.volume);
                    break;
                case 'schedule_update':
                    this.notifyScheduleUpdate(message.data.schedule);
                    break;
                case 'global_status_update':
                    this.notifyGlobalStatusUpdate(message.data.is_on);
                    break;
                case 'alarm_update':
                    this.notifyAlarmUpdate(message.data.alarms);
                    break;
                case 'system_shutdown':
                    this.notifyShutdown();
                    break;
                default:
                    console.warn('Unknown WebSocket message type:', message.type);
            }
        } catch (error) {
            console.error('Error handling WebSocket message:', error);
        }
    }
    
    // Notification methods
    private notifyAlarmStatus(isPlaying: boolean): void {
        this.alarmStatusCallbacks.forEach(callback => callback(isPlaying));
    }
    
    private notifyWhiteNoiseStatus(isPlaying: boolean): void {
        this.whiteNoiseStatusCallbacks.forEach(callback => callback(isPlaying));
    }
    
    private notifyVolumeUpdate(volume: number): void {
        this.volumeUpdateCallbacks.forEach(callback => callback(volume));
    }
    
    private notifyScheduleUpdate(schedule: string): void {
        this.scheduleUpdateCallbacks.forEach(callback => callback(schedule));
    }
    
    private notifyGlobalStatusUpdate(isOn: boolean): void {
        this.globalStatusUpdateCallbacks.forEach(callback => callback(isOn));
    }
    
    private notifyAlarmUpdate(alarms: Alarm[]): void {
        this.alarmUpdateCallbacks.forEach(callback => callback(alarms));
    }
    
    private notifyShutdown(): void {
        // First notify all registered callbacks
        this.shutdownCallbacks.forEach(callback => callback());
        
        // Then display the shutdown screen after a short delay
        setTimeout(() => {
            displayShutdownScreen();
        }, 500);
    }
    
    private notifyConnectionStatus(isConnected: boolean): void {
        this.connectionStatusCallbacks.forEach(callback => callback(isConnected));
    }
    
    // Registration methods for callbacks
    public onAlarmStatus(callback: AlarmStatusCallback): () => void {
        this.alarmStatusCallbacks.push(callback);
        return () => {
            this.alarmStatusCallbacks = this.alarmStatusCallbacks.filter(cb => cb !== callback);
        };
    }
    
    public onWhiteNoiseStatus(callback: WhiteNoiseStatusCallback): () => void {
        this.whiteNoiseStatusCallbacks.push(callback);
        return () => {
            this.whiteNoiseStatusCallbacks = this.whiteNoiseStatusCallbacks.filter(cb => cb !== callback);
        };
    }
    
    public onVolumeUpdate(callback: VolumeUpdateCallback): () => void {
        this.volumeUpdateCallbacks.push(callback);
        return () => {
            this.volumeUpdateCallbacks = this.volumeUpdateCallbacks.filter(cb => cb !== callback);
        };
    }
    
    public onScheduleUpdate(callback: ScheduleUpdateCallback): () => void {
        this.scheduleUpdateCallbacks.push(callback);
        return () => {
            this.scheduleUpdateCallbacks = this.scheduleUpdateCallbacks.filter(cb => cb !== callback);
        };
    }
    
    public onGlobalStatusUpdate(callback: GlobalStatusUpdateCallback): () => void {
        this.globalStatusUpdateCallbacks.push(callback);
        return () => {
            this.globalStatusUpdateCallbacks = this.globalStatusUpdateCallbacks.filter(cb => cb !== callback);
        };
    }
    
    public onAlarmUpdate(callback: AlarmUpdateCallback): () => void {
        this.alarmUpdateCallbacks.push(callback);
        return () => {
            this.alarmUpdateCallbacks = this.alarmUpdateCallbacks.filter(cb => cb !== callback);
        };
    }
    
    public onShutdown(callback: ShutdownCallback): () => void {
        this.shutdownCallbacks.push(callback);
        return () => {
            this.shutdownCallbacks = this.shutdownCallbacks.filter(cb => cb !== callback);
        };
    }
    
    public onConnectionStatus(callback: ConnectionStatusCallback): () => void {
        this.connectionStatusCallbacks.push(callback);
        // Immediately notify with current status
        callback(this.isConnected);
        return () => {
            this.connectionStatusCallbacks = this.connectionStatusCallbacks.filter(cb => cb !== callback);
        };
    }
    
    // Utility method to check if connected
    public isWebSocketConnected(): boolean {
        return this.isConnected;
    }
}

// Create a singleton instance
const websocketService = new WebSocketService();

export default websocketService;
