import { useState, useEffect } from 'react';
import { getWhiteNoiseStatus, adjustVolume, getVolume } from '../services/api';
import { useDebounce } from './useDebounce';

export const useAudio = () => {
    const [isPlaying, setIsPlaying] = useState(false);
    const [isWhiteNoiseActive, setIsWhiteNoiseActive] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [volume, setVolume] = useState(50); // Default volume to 50%
    const debouncedVolume = useDebounce(volume, 300); // 300ms debounce delay

    // Fetch white noise status and volume on component mount
    useEffect(() => {
        const fetchInitialState = async () => {
            try {
                setIsLoading(true);
                // Fetch white noise status
                const status = await getWhiteNoiseStatus();
                setIsWhiteNoiseActive(status.is_playing);
                
                // Fetch current volume
                const volumeData = await getVolume();
                setVolume(volumeData.volume);
            } catch (error) {
                console.error('Error fetching initial audio state:', error);
                // Don't show toast for initial load error to avoid overwhelming the user
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
    
    // Send API request only when debounced volume changes
    useEffect(() => {
        const updateVolume = async () => {
            try {
                await adjustVolume(debouncedVolume);
            } catch (error) {
                console.error('Error adjusting volume:', error);
            }
        };
        
        updateVolume();
    }, [debouncedVolume]);

    return {
        isPlaying,
        setIsPlaying,
        isWhiteNoiseActive,
        setIsWhiteNoiseActive,
        isLoading,
        volume,
        setVolume,
        handleVolumeChange
    };
};
