import { FC, FormEvent, Dispatch, SetStateAction } from 'react';
import { ThemeProvider } from '@mui/material/styles';
import { TimePicker } from '@mui/x-date-pickers/TimePicker';
import dayjs from 'dayjs';
import { Theme } from '@mui/material/styles';

const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"] as const;

interface AlarmFormProps {
    selectedTime: dayjs.Dayjs | null;
    setSelectedTime: (time: dayjs.Dayjs | null) => void;
    days: number[];
    setDays: Dispatch<SetStateAction<number[]>>;
    schedule: "a" | "b";
    setSchedule: (schedule: "a" | "b") => void;
    handleSetAlarm: () => Promise<void>;
    darkTheme: Theme;
}

export const AlarmForm: FC<AlarmFormProps> = ({
    selectedTime,
    setSelectedTime,
    days,
    setDays,
    schedule,
    setSchedule,
    handleSetAlarm,
    darkTheme
}) => {
    const toggleDay = (day: number) => {
        setDays((prev) => 
            prev.includes(day) 
                ? prev.filter((d: number) => d !== day)
                : [...prev, day].sort()
        );
    };

    return (
        <form onSubmit={(e: FormEvent) => {
            e.preventDefault();
            handleSetAlarm();
        }} className="mb-8 p-4 bg-gray-800 rounded-lg shadow">
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
                    onClick={() => setSchedule("a")}
                    className={`schedule-button primary ${schedule === "a" ? 'selected' : ''}`}
                >
                    Primary Schedule
                </button>
                <button
                    type="button"
                    onClick={() => setSchedule("b")}
                    className={`schedule-button secondary ${schedule === "b" ? 'selected' : ''}`}
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
