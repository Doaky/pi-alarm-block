import { useState } from 'react';

export const useAudio = () => {
    const [isPlaying, setIsPlaying] = useState(false);
    const [isWhiteNoiseActive, setIsWhiteNoiseActive] = useState(false);

    return {
        isPlaying,
        setIsPlaying,
        isWhiteNoiseActive,
        setIsWhiteNoiseActive
    };
};
