import { FC } from 'react';
import { toast } from 'react-toastify';

type ScheduleType = "a" | "b" | "off";

interface ScheduleControlsProps {
    currentSchedule: ScheduleType;
    setCurrentSchedule: (schedule: ScheduleType) => void;
}

export const ScheduleControls: FC<ScheduleControlsProps> = ({ currentSchedule, setCurrentSchedule }) => {
    const handleScheduleChange = async (schedule: ScheduleType) => {
        try {
            const response = await fetch("/api/v1/schedule", {
                method: "PUT",
                body: JSON.stringify({ schedule }),
                headers: { "Content-Type": "application/json" }
            });
            
            if (!response.ok) throw new Error("Failed to update schedule");
            
            setCurrentSchedule(schedule);
            const scheduleDisplay = schedule === "a" ? "Primary" : schedule === "b" ? "Secondary" : "Off";
            toast.success(`Switched to ${scheduleDisplay}`);
        } catch (err) {
            toast.error("Failed to update schedule");
            console.error("Error updating schedule:", err);
        }
    };

    return (
        <div className="mb-8 p-4 bg-gray-800 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4 title-font">Schedule Control</h2>
            <div className="grid grid-cols-3 gap-4">
                <button
                    onClick={() => handleScheduleChange('a')}
                    className={`schedule-button primary ${currentSchedule === 'a' ? 'selected' : ''}`}
                >
                    Primary
                </button>
                <button
                    onClick={() => handleScheduleChange('b')}
                    className={`schedule-button secondary ${currentSchedule === 'b' ? 'selected' : ''}`}
                >
                    Secondary
                </button>
                <button
                    onClick={() => handleScheduleChange('off')}
                    className={`schedule-button off ${currentSchedule === 'off' ? 'selected' : ''}`}
                >
                    Off
                </button>
            </div>
        </div>
    );
};
