import { useState, useEffect } from 'react';
import { getWhiteNoiseStatus, adjustVolume } from '../services/api';
import { useDebounce } from './useDebounce';

export const useAudio = () => {
    const [isPlaying, setIsPlaying] = useState(false);
    const [isWhiteNoiseActive, setIsWhiteNoiseActive] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [volume, setVolume] = useState(50); // Default volume to 50%
    const debouncedVolume = useDebounce(volume, 300); // 300ms debounce delay

    // Fetch white noise status on component mount
    useEffect(() => {
        const fetchWhiteNoiseStatus = async () => {
            try {
                setIsLoading(true);
                const status = await getWhiteNoiseStatus();
                setIsWhiteNoiseActive(status.is_playing);
            } catch (error) {
                console.error('Error fetching white noise status:', error);
                // Don't show toast for initial load error to avoid overwhelming the user
            } finally {
                setIsLoading(false);
            }
        };

        fetchWhiteNoiseStatus();
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
