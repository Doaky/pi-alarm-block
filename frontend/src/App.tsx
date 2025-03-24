import { useState, useEffect } from "react";
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { createTheme, ThemeProvider } from '@mui/material/styles';
import { Divider } from '@mui/material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { TimePicker } from '@mui/x-date-pickers/TimePicker';
import dayjs from 'dayjs';
import './styles.css';

// Define the expected structure of an alarm
interface Alarm {
    id: string;
    hour: number;
    minute: number;
    days: number[];
    is_primary_schedule: boolean;
    active: boolean;
}

type ScheduleType = "a" | "b" | "off";

// Day name mapping for better display
const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"] as const;

// Format time in 12-hour format with AM/PM
function formatTime(hour: number, minute: number): string {
    const period = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 || 12;
    return `${displayHour}:${minute.toString().padStart(2, '0')} ${period}`;
}

// Parse dayjs object to { hour: number, minute: number }
function parseTime(time: dayjs.Dayjs | null): { hour: number, minute: number } {
    if (!time) return { hour: 0, minute: 0 };
    return { hour: time.hour(), minute: time.minute() };
}

const darkTheme = createTheme({
    palette: {
      mode: 'dark',
    },
});
  
const App = () => {
    // Alarm states
    const [alarms, setAlarms] = useState<Alarm[]>([]);
    const [selectedAlarms, setSelectedAlarms] = useState<Set<string>>(new Set());

    // Form states
    const [selectedTime, setSelectedTime] = useState<dayjs.Dayjs | null>(dayjs());
    const [days, setDays] = useState<number[]>([]);
    const [isPrimary, setIsPrimary] = useState(true);

    // Global states
    const [currentSchedule, setCurrentSchedule] = useState<ScheduleType>("a");
    const [isLoading, setIsLoading] = useState(true);

    // Audio states
    const [isPlaying, setIsPlaying] = useState(false);
    const [isWhiteNoiseActive, setIsWhiteNoiseActive] = useState(false);

    useEffect(() => {
        Promise.all([
            fetch("/alarms")
                .then(res => res.json())
                .catch(err => {
                    toast.error("Failed to fetch alarms");
                    console.error("Error fetching alarms:", err);
                    return [];
                }),
            fetch("/get_schedule")
                .then(res => res.json())
                .catch(err => {
                    toast.error("Failed to fetch schedule");
                    console.error("Error fetching schedule:", err);
                    return { schedule: "a" };
                })
        ]).then(([alarmsData, scheduleData]) => {
            setAlarms(alarmsData);
            setCurrentSchedule(scheduleData.schedule);
            setIsLoading(false);
        });
    }, []);

    const toggleDay = (day: number) => {
        setDays(prev => 
            prev.includes(day) 
                ? prev.filter(d => d !== day)
                : [...prev, day].sort()
        );
    };

    const handleSetAlarm = async (e: React.FormEvent) => {
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
            setAlarms(prev => [...prev, data.alarm]);
            toast.success("Alarm set successfully");
            
            // Reset form
            setDays([]);
            setSelectedTime(dayjs());
        } catch (err) {
            toast.error("Failed to set alarm");
            console.error("Error setting alarm:", err);
        }
    };

    const handleScheduleChange = async (schedule: ScheduleType) => {
        try {
            const response = await fetch("/set_schedule", {
                method: "POST",
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

    const toggleAlarmSelection = (alarmId: string) => {
        setSelectedAlarms(prev =>
            prev.has(alarmId) 
                ? new Set([...prev].filter(id => id !== alarmId))
                : new Set(prev.add(alarmId))
        );
    };

    const handleDeleteSelectedAlarms = async () => {
        const alarmIds = Array.from(selectedAlarms);

        if (alarmIds.length === 0) {
            toast.warning("Please select alarms to delete");
            return;
        }

        try {
            const response = await fetch("/alarms", {
                method: "DELETE",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(alarmIds),
            });
            
            if (!response.ok) throw new Error("Failed to delete alarms");
            
            setAlarms(prev => prev.filter(alarm => !alarmIds.includes(alarm.id)));
            setSelectedAlarms(new Set());
            toast.success("Selected alarms deleted");
        } catch (err) {
            toast.error("Failed to delete alarms");
            console.error("Error deleting alarms:", err);
        }
    };

    const toggleAlarmActive = async (alarm: Alarm) => {
        const updatedAlarm = { ...alarm, active: !alarm.active };
        try {
            const response = await fetch("/set-alarm", {
                method: "PUT",
                body: JSON.stringify(updatedAlarm),
                headers: { "Content-Type": "application/json" }
            });
            
            if (!response.ok) throw new Error("Failed to update alarm");
            
            setAlarms(prev => prev.map(a => a.id === alarm.id ? updatedAlarm : a));
            toast.success(`Alarm ${updatedAlarm.active ? "activated" : "deactivated"}`);
        } catch (err) {
            toast.error("Failed to update alarm");
            console.error("Error updating alarm:", err);
        }
    };

    const handlePlayAlarm = async () => {
        try {
            const response = await fetch("/play-alarm", { method: "POST" });
            if (!response.ok) throw new Error("Failed to play alarm");
            setIsPlaying(true);
        } catch (err) {
            toast.error("Failed to play alarm");
            console.error("Error playing alarm:", err);
        }
    };

    const handleStopAlarm = async () => {
        try {
            const response = await fetch("/stop-alarm", { method: "POST" });
            if (!response.ok) throw new Error("Failed to stop alarm");
            setIsPlaying(false);
        } catch (err) {
            toast.error("Failed to stop alarm");
            console.error("Error stopping alarm:", err);
        }
    };

    const handlePlayWhiteNoise = async () => {
        try {
            const response = await fetch("/white-noise/play", { method: "POST" });
            if (!response.ok) throw new Error("Failed to play white noise");
            setIsWhiteNoiseActive(true);
        } catch (err) {
            toast.error("Failed to play white noise");
            console.error("Error playing white noise:", err);
        }
    };

    const handleStopWhiteNoise = async () => {
        try {
            const response = await fetch("/white-noise/stop", { method: "POST" });
            if (!response.ok) throw new Error("Failed to stop white noise");
            setIsWhiteNoiseActive(false);
        } catch (err) {
            toast.error("Failed to stop white noise");
            console.error("Error stopping white noise:", err);
        }
    };

    // Sort alarms by time and schedule
    const sortedAlarms = [...alarms].sort((a, b) => {
        if (a.is_primary_schedule !== b.is_primary_schedule) {
            return a.is_primary_schedule ? -1 : 1;
        }
        return a.hour * 60 + a.minute - (b.hour * 60 + b.minute);
    });

    return (
        <LocalizationProvider dateAdapter={AdapterDayjs}>
            <div className="min-h-screen p-4 bg-gray-900 text-white body-font">
                <div className="max-w-4xl mx-auto">
                    <div className="mb-8">
                        <h1 className="text-3xl font-bold title-font">Alarm Block</h1>
                    </div>

                    {/* Schedule Controls */}
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

                    {/* Set Alarm Form */}
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

                    {/* Alarms List */}
                    <div className="mb-8 p-4 bg-gray-800 rounded-lg shadow">
                        <h2 className="text-xl font-semibold mb-4 title-font">Alarms</h2>
                        {isLoading ? (
                            <p>Loading alarms...</p>
                        ) : sortedAlarms.length === 0 ? (
                            <p>No alarms set</p>
                        ) : (
                            <div className="space-y-2">
                                {sortedAlarms.map((alarm, index) => {
                                    const showDivider = index > 0 && alarm.is_primary_schedule !== sortedAlarms[index - 1].is_primary_schedule;
                                    return (
                                        <div key={alarm.id}>
                                            {showDivider && <Divider className="my-4 border-gray-600" />}
                                            <div
                                                className={`alarm-entry ${selectedAlarms.has(alarm.id) ? 'selected' : ''}`}
                                                onClick={() => toggleAlarmSelection(alarm.id)}
                                            >
                                                <div className="flex justify-between items-center">
                                                    <div>
                                                        <span className="font-semibold">
                                                            {formatTime(alarm.hour, alarm.minute)}
                                                        </span>
                                                        <span className="ml-4">
                                                            {alarm.days.map(d => DAYS[d]).join(', ')}
                                                        </span>
                                                    </div>
                                                    <div className="flex items-center gap-4">
                                                        <span className={`px-2 py-1 rounded ${
                                                            alarm.is_primary_schedule
                                                                ? 'bg-blue-500 text-white'
                                                                : 'bg-purple-500 text-white'
                                                        }`}>
                                                            {alarm.is_primary_schedule ? 'Primary' : 'Secondary'}
                                                        </span>
                                                        <div
                                                            className={`status-chip ${alarm.active ? 'active' : 'inactive'}`}
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                toggleAlarmActive(alarm);
                                                            }}
                                                        >
                                                            {alarm.active ? 'Active' : 'Inactive'}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                                <button
                                    onClick={handleDeleteSelectedAlarms}
                                    className="w-full mt-4 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed"
                                    disabled={selectedAlarms.size === 0}
                                >
                                    Delete {selectedAlarms.size > 1 ? "Alarms" : "Alarm"}
                                </button>
                            </div>
                        )}
                    </div>

                    {/* Audio Controls */}
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
                </div>
                <ToastContainer position="bottom-right" theme="dark" />
            </div>
        </LocalizationProvider>
    );
};

export default App;
