import { useState, useEffect, useRef } from 'react';
import { getWhiteNoiseStatus, adjustVolume, getVolume } from '../services/api';
import { useDebounce } from './useDebounce';

export const useAudio = () => {
    const [isPlaying, setIsPlaying] = useState(false);
    const [isWhiteNoiseActive, setIsWhiteNoiseActive] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [volume, setVolume] = useState(25); // Start with 25%, will be updated from backend
    const debouncedVolume = useDebounce(volume, 300); // 300ms debounce delay
    const initialFetchCompleted = useRef(false); // Track if we've completed the initial fetch

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
