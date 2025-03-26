import { FC, FormEvent, Dispatch, SetStateAction } from 'react';
import { toast } from 'react-toastify';
import { ThemeProvider } from '@mui/material/styles';
import { TimePicker } from '@mui/x-date-pickers/TimePicker';
import dayjs from 'dayjs';
import { Alarm } from '../types/index';

const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"] as const;

interface AlarmFormProps {
    selectedTime: dayjs.Dayjs | null;
    setSelectedTime: (time: dayjs.Dayjs | null) => void;
    days: number[];
    setDays: Dispatch<SetStateAction<number[]>>;
    isPrimary: boolean;
    setIsPrimary: (isPrimary: boolean) => void;
    setAlarms: Dispatch<SetStateAction<Alarm[]>>;
    darkTheme: any;
}

export const AlarmForm: FC<AlarmFormProps> = ({
    selectedTime,
    setSelectedTime,
    days,
    setDays,
    isPrimary,
    setIsPrimary,
    setAlarms,
    darkTheme
}) => {
    const toggleDay = (day: number) => {
        setDays((prev) => 
            prev.includes(day) 
                ? prev.filter((d: number) => d !== day)
                : [...prev, day].sort()
        );
    };

    const parseTime = (time: dayjs.Dayjs | null): { hour: number, minute: number } => {
        if (!time) return { hour: 0, minute: 0 };
        return { hour: time.hour(), minute: time.minute() };
    };

    const handleSetAlarm = async (e: FormEvent) => {
        e.preventDefault();

        if (!selectedTime) {
            toast.warning("Please select a time");
            return;
        }

        if (days.length === 0) {
            toast.warning("Please select at least one day");
            return;
        }

        const { hour, minute } = parseTime(selectedTime);

        const newAlarm = {
            id: crypto.randomUUID(),
            hour,
            minute,
            days: [...days].sort(),
            is_primary_schedule: isPrimary,
            active: true,
        };

        try {
            const response = await fetch("/set-alarm", {
                method: "PUT",
                body: JSON.stringify(newAlarm),
                headers: { "Content-Type": "application/json" }
            });
            
            if (!response.ok) throw new Error("Failed to set alarm");
            
            const data = await response.json();
            setAlarms((prev) => [...prev, data.alarm]);
            toast.success("Alarm set successfully");
            
            // Reset form
            setDays([]);
            setSelectedTime(dayjs());
        } catch (err) {
            toast.error("Failed to set alarm");
            console.error("Error setting alarm:", err);
        }
    };

    return (
        <form onSubmit={handleSetAlarm} className="mb-8 p-4 bg-gray-800 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4 title-font">Set New Alarm</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                    <label className="block mb-2">Time:</label>
                    <ThemeProvider theme={darkTheme}>
                        <TimePicker
                            value={selectedTime}
                            onChange={(newValue) => setSelectedTime(newValue)}
                            slotProps={{
                                textField: {
                                    className: "bg-gray-700 rounded text-white h-14",
                                    sx: {
                                        '& .MuiInputBase-input': {
                                            color: 'white',
                                        },
                                        '& .MuiOutlinedInput-notchedOutline': {
                                            borderColor: 'rgba(255, 255, 255, 0.23)',
                                        },
                                        '&:hover .MuiOutlinedInput-notchedOutline': {
                                            borderColor: 'rgba(255, 255, 255, 0.23)',
                                        },
                                        '& .MuiIconButton-root': {
                                            color: 'white',
                                        },
                                        '& .MuiPaper-root': {
                                            backgroundColor: 'rgb(31, 41, 55)',
                                            color: 'white',
                                        },
                                        '& .MuiClock-root': {
                                            backgroundColor: 'rgb(31, 41, 55)',
                                            color: 'white',
                                        },
                                        '& .MuiClockNumber-root': {
                                            color: 'white',
                                        },
                                        '& .MuiClockPointer-root': {
                                            backgroundColor: 'rgb(59, 130, 246)',
                                        },
                                        '& .MuiClockPointer-thumb': {
                                            backgroundColor: 'rgb(59, 130, 246)',
                                            borderColor: 'rgb(59, 130, 246)',
                                        },
                                        '& .MuiClock-pin': {
                                            backgroundColor: 'rgb(59, 130, 246)',
                                        }
                                    }
                                }
                            }}
                        />
                    </ThemeProvider>
                </div>
                <div>
                    <label className="block mb-2">Days:</label>
                    <div className="flex flex-wrap gap-2">
                        {DAYS.map((day, index) => (
                            <button
                                key={day}
                                type="button"
                                onClick={() => toggleDay(index)}
                                className={`day-button ${
                                    days.includes(index)
                                        ? 'bg-blue-500 text-white'
                                        : 'bg-gray-700'
                                }`}
                            >
                                {day}
                            </button>
                        ))}
                    </div>
                </div>
            </div>
            <div className="grid grid-cols-2 gap-4 mb-4">
                <button
                    type="button"
                    onClick={() => setIsPrimary(true)}
                    className={`schedule-button primary ${isPrimary ? 'selected' : ''}`}
                >
                    Primary Schedule
                </button>
                <button
                    type="button"
                    onClick={() => setIsPrimary(false)}
                    className={`schedule-button secondary ${!isPrimary ? 'selected' : ''}`}
                >
                    Secondary Schedule
                </button>
            </div>
            <button
                type="submit"
                className="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
                Set Alarm
            </button>
        </form>
    );
};
