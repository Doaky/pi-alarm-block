import { FC } from 'react';
import { toast } from 'react-toastify';

interface AudioControlsProps {
    isPlaying: boolean;
    setIsPlaying: (isPlaying: boolean) => void;
    isWhiteNoiseActive: boolean;
    setIsWhiteNoiseActive: (isActive: boolean) => void;
}

export const AudioControls: FC<AudioControlsProps> = ({
    isPlaying,
    setIsPlaying,
    isWhiteNoiseActive,
    setIsWhiteNoiseActive
}) => {
    const handlePlayAlarm = async () => {
        try {
            const response = await fetch("/api/v1/play-alarm", { method: "POST" });
            if (!response.ok) throw new Error("Failed to play alarm");
            setIsPlaying(true);
        } catch (err) {
            toast.error("Failed to play alarm");
            console.error("Error playing alarm:", err);
        }
    };

    const handleStopAlarm = async () => {
        try {
            const response = await fetch("/api/v1/stop-alarm", { method: "POST" });
            if (!response.ok) throw new Error("Failed to stop alarm");
            setIsPlaying(false);
        } catch (err) {
            toast.error("Failed to stop alarm");
            console.error("Error stopping alarm:", err);
        }
    };

    const handlePlayWhiteNoise = async () => {
        try {
            const response = await fetch("/api/v1/white-noise", { 
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action: "play" })
            });
            if (!response.ok) throw new Error("Failed to play white noise");
            setIsWhiteNoiseActive(true);
        } catch (err) {
            toast.error("Failed to play white noise");
            console.error("Error playing white noise:", err);
        }
    };

    const handleStopWhiteNoise = async () => {
        try {
            const response = await fetch("/api/v1/white-noise", { 
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action: "stop" })
            });
            if (!response.ok) throw new Error("Failed to stop white noise");
            setIsWhiteNoiseActive(false);
        } catch (err) {
            toast.error("Failed to stop white noise");
            console.error("Error stopping white noise:", err);
        }
    };

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-gray-800 rounded-lg shadow">
                <h2 className="text-xl font-semibold mb-4 title-font">Alarm Sound</h2>
                <button
                    onClick={isPlaying ? handleStopAlarm : handlePlayAlarm}
                    className={`w-full px-4 py-2 rounded ${
                        isPlaying
                            ? 'bg-red-500 hover:bg-red-600'
                            : 'bg-green-500 hover:bg-green-600'
                    } text-white`}
                >
                    {isPlaying ? 'Stop Alarm' : 'Test Alarm'}
                </button>
            </div>
            <div className="p-4 bg-gray-800 rounded-lg shadow">
                <h2 className="text-xl font-semibold mb-4 title-font">White Noise</h2>
                <button
                    onClick={isWhiteNoiseActive ? handleStopWhiteNoise : handlePlayWhiteNoise}
                    className={`w-full px-4 py-2 rounded ${
                        isWhiteNoiseActive
                            ? 'bg-red-500 hover:bg-red-600'
                            : 'bg-green-500 hover:bg-green-600'
                    } text-white`}
                >
                    {isWhiteNoiseActive ? 'Stop White Noise' : 'Play White Noise'}
                </button>
            </div>
        </div>
    );
};
