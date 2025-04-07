import { useState, useEffect, useRef } from 'react';
import { getWhiteNoiseStatus, adjustVolume, getVolume, playWhiteNoise, stopWhiteNoise, getAlarmStatus } from '../services/api';
import { useDebounce } from './useDebounce';
import useWebSocket from './useWebSocket';

export const useAudio = () => {
    const [isPlaying, setIsPlaying] = useState(false);
    const [isWhiteNoiseActive, setIsWhiteNoiseActive] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [volume, setVolume] = useState(25); // Start with 25%, will be updated from backend
    const debouncedVolume = useDebounce(volume, 300); // 300ms debounce delay
    const initialFetchCompleted = useRef(false); // Track if we've completed the initial fetch
    
    // Setup WebSocket listeners for real-time updates
    useWebSocket({
        onAlarmStatus: (isAlarmPlaying) => {
            setIsPlaying(isAlarmPlaying);
            console.log(`Alarm status updated to ${isAlarmPlaying ? 'playing' : 'stopped'} via WebSocket`);
        },
        onWhiteNoiseStatus: (isWhiteNoisePlaying) => {
            setIsWhiteNoiseActive(isWhiteNoisePlaying);
            console.log(`White noise status updated to ${isWhiteNoisePlaying ? 'playing' : 'stopped'} via WebSocket`);
        },
        onVolumeUpdate: (newVolume) => {
            // Only update if it's different from our current volume to avoid loops
            if (Math.abs(newVolume - volume) > 1) {
                setVolume(newVolume);
                console.log(`Volume updated to ${newVolume} via WebSocket`);
            }
        },
        onShutdown: () => {
            console.log('System shutdown notification received');
            // The WebSocket service will handle displaying the shutdown screen
        }
    });

    // Fetch audio states on component mount
    useEffect(() => {
        const fetchInitialState = async () => {
            try {
                setIsLoading(true);
                // Fetch white noise status
                const whiteNoiseStatus = await getWhiteNoiseStatus();
                setIsWhiteNoiseActive(whiteNoiseStatus.is_playing);
                
                // Fetch alarm status
                const alarmStatus = await getAlarmStatus();
                setIsPlaying(alarmStatus.is_playing);
                console.log(`Initial alarm status: ${alarmStatus.is_playing ? 'playing' : 'stopped'}`);
                
                // Fetch current volume
                const volumeData = await getVolume();
                setVolume(volumeData.volume);
                
                // Mark initial fetch as completed
                initialFetchCompleted.current = true;
            } catch (error) {
                console.error('Error fetching initial audio state:', error);
                // Don't show toast for initial load error to avoid overwhelming the user
                // Still mark as completed even on error to prevent being stuck
                initialFetchCompleted.current = true;
            } finally {
                setIsLoading(false);
            }
        };

        fetchInitialState();
    }, []);

    // Update local volume state immediately for responsive UI
    const handleVolumeChange = (newVolume: number) => {
        setVolume(newVolume);
    };
    
    // Send API request only when debounced volume changes AND after initial fetch
    useEffect(() => {
        const updateVolume = async () => {
            // Skip the API call if we haven't completed the initial fetch yet
            if (!initialFetchCompleted.current) {
                return;
            }
            
            try {
                await adjustVolume(debouncedVolume);
            } catch (error) {
                console.error('Error adjusting volume:', error);
            }
        };
        
        updateVolume();
    }, [debouncedVolume]);

    // Add methods to play and stop white noise
    const handlePlayWhiteNoise = async () => {
        try {
            await playWhiteNoise();
            setIsWhiteNoiseActive(true);
        } catch (error) {
            console.error('Error playing white noise:', error);
        }
    };

    const handleStopWhiteNoise = async () => {
        try {
            await stopWhiteNoise();
            setIsWhiteNoiseActive(false);
        } catch (error) {
            console.error('Error stopping white noise:', error);
        }
    };

    return {
        isPlaying,
        setIsPlaying,
        isWhiteNoiseActive,
        setIsWhiteNoiseActive,
        isLoading,
        volume,
        setVolume,
        handleVolumeChange,
        handlePlayWhiteNoise,
        handleStopWhiteNoise
    };
};
