import { useState, useEffect } from 'react';
import { getWhiteNoiseStatus } from '../services/api';

export const useAudio = () => {
    const [isPlaying, setIsPlaying] = useState(false);
    const [isWhiteNoiseActive, setIsWhiteNoiseActive] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

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

    return {
        isPlaying,
        setIsPlaying,
        isWhiteNoiseActive,
        setIsWhiteNoiseActive,
        isLoading
    };
};
