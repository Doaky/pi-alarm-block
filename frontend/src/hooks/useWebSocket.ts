import { useEffect, useState } from 'react';
import websocketService from '../services/websocket';
import { Alarm } from '../types';

// Define the hook options interface
interface UseWebSocketOptions {
  onAlarmStatus?: (isPlaying: boolean) => void;
  onWhiteNoiseStatus?: (isPlaying: boolean) => void;
  onVolumeUpdate?: (volume: number) => void;
  onScheduleUpdate?: (schedule: string) => void;
  onGlobalStatusUpdate?: (isOn: boolean) => void;
  onAlarmUpdate?: (alarms: Alarm[]) => void;
  onShutdown?: () => void;
  onConnectionStatus?: (isConnected: boolean) => void;
}

/**
 * Hook for interacting with WebSocket service
 * 
 * @param options - Callback functions for different WebSocket events
 * @returns Object containing connection status and manual reconnect function
 */
export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const [isConnected, setIsConnected] = useState(websocketService.isWebSocketConnected());

  useEffect(() => {
    // Register all callbacks
    const cleanupFunctions: (() => void)[] = [];

    if (options.onAlarmStatus) {
      cleanupFunctions.push(websocketService.onAlarmStatus(options.onAlarmStatus));
    }

    if (options.onWhiteNoiseStatus) {
      cleanupFunctions.push(websocketService.onWhiteNoiseStatus(options.onWhiteNoiseStatus));
    }

    if (options.onVolumeUpdate) {
      cleanupFunctions.push(websocketService.onVolumeUpdate(options.onVolumeUpdate));
    }

    if (options.onScheduleUpdate) {
      cleanupFunctions.push(websocketService.onScheduleUpdate(options.onScheduleUpdate));
    }

    if (options.onGlobalStatusUpdate) {
      cleanupFunctions.push(websocketService.onGlobalStatusUpdate(options.onGlobalStatusUpdate));
    }

    if (options.onAlarmUpdate) {
      cleanupFunctions.push(websocketService.onAlarmUpdate(options.onAlarmUpdate));
    }

    if (options.onShutdown) {
      cleanupFunctions.push(websocketService.onShutdown(options.onShutdown));
    }

    // Always track connection status
    cleanupFunctions.push(
      websocketService.onConnectionStatus((connected) => {
        setIsConnected(connected);
        if (options.onConnectionStatus) {
          options.onConnectionStatus(connected);
        }
      })
    );

    // Clean up all subscriptions when component unmounts
    return () => {
      cleanupFunctions.forEach(cleanup => cleanup());
    };
  }, [options]);

  // Return connection status and manual reconnect function
  return {
    isConnected,
    reconnect: () => websocketService.connect()
  };
};

export default useWebSocket;
