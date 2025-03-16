import { useState, useEffect } from "react";
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

// Define the expected structure of an alarm
interface Alarm {
    id: string;
    hour: number;
    minute: number;
    days: number[];
    is_primary_schedule: boolean;
    active: boolean;
}

// Day name mapping for better display
const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"] as const;

const App = () => {
    // Alarm states
    const [alarms, setAlarms] = useState<Alarm[]>([]);
    const [selectedAlarms, setSelectedAlarms] = useState<Set<string>>(new Set());

    // Form states
    const [hour, setHour] = useState(7);
    const [minute, setMinute] = useState(30);
    const [days, setDays] = useState<number[]>([]);
    const [isPrimary, setIsPrimary] = useState(true);
    const [active, setActive] = useState(true);

    // Global states
    const [isPrimarySchedule, setIsPrimarySchedule] = useState(true);
    const [globalStatus, setGlobalStatus] = useState(true);
    const [isLoading, setIsLoading] = useState(true);

    // Audio states
    const [isPlaying, setIsPlaying] = useState(false);
    const [isWhiteNoiseActive, setIsWhiteNoiseActive] = useState(false);

    useEffect(() => {
        Promise.all([
            // Fetch alarms
            fetch("/alarms")
                .then(res => res.json())
                .catch(err => {
                    toast.error("Failed to fetch alarms");
                    console.error("Error fetching alarms:", err);
                    return [];
                }),
            // Fetch schedule state
            fetch("/get_schedule")
                .then(res => res.json())
                .catch(err => {
                    toast.error("Failed to fetch schedule");
                    console.error("Error fetching schedule:", err);
                    return { is_primary_schedule: true };
                }),
            // Fetch global status
            fetch("/get_global_status")
                .then(res => res.json())
                .catch(err => {
                    toast.error("Failed to fetch global status");
                    console.error("Error fetching global status:", err);
                    return { is_global_on: true };
                })
        ]).then(([alarmsData, scheduleData, statusData]) => {
            setAlarms(alarmsData);
            setIsPrimarySchedule(scheduleData.is_primary_schedule);
            setGlobalStatus(statusData.is_global_on);
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

        if (days.length === 0) {
            toast.warning("Please select at least one day");
            return;
        }

        const newAlarm = {
            id: crypto.randomUUID(),
            hour,
            minute,
            days: [...days].sort(),
            is_primary_schedule: isPrimary,
            active,
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
            setHour(7);
            setMinute(30);
        } catch (err) {
            toast.error("Failed to set alarm");
            console.error("Error setting alarm:", err);
        }
    };

    const handleGlobalStatusChange = async (newStatus: boolean) => {
        try {
            const response = await fetch("/set_global_status", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ is_global_on: newStatus }),
            });
            
            if (!response.ok) throw new Error("Failed to update global status");
            
            setGlobalStatus(newStatus);
            toast.success(`Alarms ${newStatus ? "enabled" : "disabled"} globally`);
        } catch (err) {
            toast.error("Failed to update global status");
            console.error("Error updating global status:", err);
        }
    };

    const handleScheduleChange = async (isPrimary: boolean) => {
        try {
            const response = await fetch("/set_schedule", {
                method: "POST",
                body: JSON.stringify({ is_primary: isPrimary }),
                headers: { "Content-Type": "application/json" }
            });
            
            if (!response.ok) throw new Error("Failed to update schedule");
            
            setIsPrimarySchedule(isPrimary);
            toast.success(`Switched to ${isPrimary ? "primary" : "secondary"} schedule`);
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
                body: JSON.stringify({ alarm_ids: alarmIds }),
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

    const toggleAlarm = async () => {
        try {
            const response = await fetch(isPlaying ? "/stop-alarm" : "/play-alarm", {
                method: "POST",
                headers: { "Content-Type": "application/json" }
            });
            
            if (!response.ok) throw new Error(`Failed to ${isPlaying ? "stop" : "play"} alarm`);
            
            setIsPlaying(!isPlaying);
            toast.success(`Alarm ${isPlaying ? "stopped" : "started"}`);
        } catch (err) {
            toast.error(`Failed to ${isPlaying ? "stop" : "play"} alarm`);
            console.error("Error controlling alarm:", err);
        }
    };

    const toggleWhiteNoise = async () => {
        try {
            const response = await fetch(isWhiteNoiseActive ? "/stop-white-noise" : "/play-white-noise", {
                method: "POST",
                headers: { "Content-Type": "application/json" }
            });
            
            if (!response.ok) throw new Error(`Failed to ${isWhiteNoiseActive ? "stop" : "play"} white noise`);
            
            setIsWhiteNoiseActive(!isWhiteNoiseActive);
            toast.success(`White noise ${isWhiteNoiseActive ? "stopped" : "started"}`);
        } catch (err) {
            toast.error(`Failed to ${isWhiteNoiseActive ? "stop" : "play"} white noise`);
            console.error("Error controlling white noise:", err);
        }
    };

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-100">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-100 py-8 px-4">
            <div className="max-w-4xl mx-auto space-y-8">
                {/* Settings Section */}
                <section className="bg-white rounded-lg shadow-md p-6">
                    <h2 className="text-2xl font-bold mb-6 text-gray-800">Settings</h2>
                    
                    {/* Schedule Type */}
                    <div className="mb-6">
                        <h3 className="text-lg font-semibold mb-3 text-gray-700">Schedule Type</h3>
                        <div className="flex gap-6">
                            {["Primary", "Secondary"].map((schedule, idx) => (
                                <label key={schedule} className="flex items-center space-x-2 cursor-pointer">
                                    <input
                                        type="radio"
                                        checked={idx === 0 ? isPrimarySchedule : !isPrimarySchedule}
                                        onChange={() => handleScheduleChange(idx === 0)}
                                        className="form-radio h-4 w-4 text-blue-500"
                                    />
                                    <span className="text-gray-700">{schedule} Schedule</span>
                                </label>
                            ))}
                        </div>
                    </div>

                    {/* Global Status */}
                    <div className="mb-6">
                        <label className="flex items-center space-x-2 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={globalStatus}
                                onChange={(e) => handleGlobalStatusChange(e.target.checked)}
                                className="form-checkbox h-4 w-4 text-blue-500 rounded"
                            />
                            <span className="text-gray-700">
                                Global Status: <span className={globalStatus ? "text-green-500" : "text-red-500"}>
                                    {globalStatus ? "Enabled" : "Disabled"}
                                </span>
                            </span>
                        </label>
                    </div>

                    {/* Sound Controls */}
                    <div className="flex gap-4">
                        <button
                            onClick={toggleAlarm}
                            className={`px-4 py-2 rounded-md font-medium transition-colors ${
                                isPlaying
                                    ? "bg-red-500 hover:bg-red-600 text-white"
                                    : "bg-blue-500 hover:bg-blue-600 text-white"
                            }`}
                        >
                            {isPlaying ? "Stop Alarm" : "Test Alarm"}
                        </button>
                        <button
                            onClick={toggleWhiteNoise}
                            className={`px-4 py-2 rounded-md font-medium transition-colors ${
                                isWhiteNoiseActive
                                    ? "bg-red-500 hover:bg-red-600 text-white"
                                    : "bg-blue-500 hover:bg-blue-600 text-white"
                            }`}
                        >
                            {isWhiteNoiseActive ? "Stop White Noise" : "Play White Noise"}
                        </button>
                    </div>
                </section>

                {/* Alarm Form Section */}
                <section className="bg-white rounded-lg shadow-md p-6">
                    <h2 className="text-2xl font-bold mb-6 text-gray-800">Add New Alarm</h2>
                    <form onSubmit={handleSetAlarm} className="space-y-6">
                        {/* Time Input */}
                        <div className="flex items-center space-x-2">
                            <label className="text-gray-700 font-medium">Time:</label>
                            <input 
                                type="number" 
                                value={hour} 
                                onChange={(e) => setHour(Math.min(23, Math.max(0, parseInt(e.target.value) || 0)))} 
                                className="w-16 px-2 py-1 border rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                min="0"
                                max="23"
                            />
                            <span className="text-gray-700">:</span>
                            <input 
                                type="number" 
                                value={minute} 
                                onChange={(e) => setMinute(Math.min(59, Math.max(0, parseInt(e.target.value) || 0)))} 
                                className="w-16 px-2 py-1 border rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                min="0"
                                max="59"
                            />
                        </div>

                        {/* Days Selection */}
                        <div>
                            <label className="text-gray-700 font-medium block mb-2">Days:</label>
                            <div className="flex flex-wrap gap-3">
                                {DAYS.map((day, index) => (
                                    <label key={day} className="flex items-center space-x-2 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={days.includes(index)}
                                            onChange={() => toggleDay(index)}
                                            className="form-checkbox h-4 w-4 text-blue-500 rounded"
                                        />
                                        <span className="text-gray-700">{day}</span>
                                    </label>
                                ))}
                            </div>
                        </div>

                        {/* Schedule Selection */}
                        <div>
                            <label className="text-gray-700 font-medium block mb-2">Schedule:</label>
                            <div className="flex gap-6">
                                {["Primary", "Secondary"].map((schedule, idx) => (
                                    <label key={schedule} className="flex items-center space-x-2 cursor-pointer">
                                        <input
                                            type="radio"
                                            name="schedule"
                                            checked={idx === 0 ? isPrimary : !isPrimary}
                                            onChange={() => setIsPrimary(idx === 0)}
                                            className="form-radio h-4 w-4 text-blue-500"
                                        />
                                        <span className="text-gray-700">{schedule}</span>
                                    </label>
                                ))}
                            </div>
                        </div>

                        {/* Active Status */}
                        <div>
                            <label className="flex items-center space-x-2 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={active}
                                    onChange={() => setActive(prev => !prev)}
                                    className="form-checkbox h-4 w-4 text-blue-500 rounded"
                                />
                                <span className="text-gray-700">Active</span>
                            </label>
                        </div>

                        <button
                            type="submit"
                            className="w-full bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 transition-colors font-medium"
                        >
                            Set Alarm
                        </button>
                    </form>
                </section>

                {/* Alarm List Section */}
                <section className="bg-white rounded-lg shadow-md p-6">
                    <h2 className="text-2xl font-bold mb-6 text-gray-800">Alarm List</h2>
                    {alarms.length === 0 ? (
                        <p className="text-gray-500 text-center py-4">No alarms set</p>
                    ) : (
                        <div className="space-y-4">
                            <ul className="space-y-2">
                                {alarms.map((alarm) => (
                                    <li
                                        key={alarm.id}
                                        className={`flex items-center p-3 rounded-md ${
                                            selectedAlarms.has(alarm.id) ? "bg-blue-50" : "hover:bg-gray-50"
                                        }`}
                                    >
                                        <input
                                            type="checkbox"
                                            checked={selectedAlarms.has(alarm.id)}
                                            onChange={() => toggleAlarmSelection(alarm.id)}
                                            className="form-checkbox h-4 w-4 text-blue-500 rounded mr-4"
                                        />
                                        <div className="flex-1">
                                            <span className="font-medium">
                                                {alarm.hour.toString().padStart(2, "0")}:
                                                {alarm.minute.toString().padStart(2, "0")}
                                            </span>
                                            <span className="mx-2">-</span>
                                            <span className="text-gray-600">
                                                {alarm.days.map(d => DAYS[d]).join(", ")}
                                            </span>
                                            <span className={`ml-4 ${alarm.active ? "text-green-500" : "text-red-500"}`}>
                                                ({alarm.active ? "Active" : "Inactive"})
                                            </span>
                                            <span className="ml-4 text-gray-500">
                                                ({alarm.is_primary_schedule ? "Primary" : "Secondary"})
                                            </span>
                                        </div>
                                    </li>
                                ))}
                            </ul>
                            <button
                                onClick={handleDeleteSelectedAlarms}
                                disabled={selectedAlarms.size === 0}
                                className={`w-full py-2 px-4 rounded-md font-medium transition-colors ${
                                    selectedAlarms.size > 0
                                        ? "bg-red-500 hover:bg-red-600 text-white"
                                        : "bg-gray-300 text-gray-500 cursor-not-allowed"
                                }`}
                            >
                                Delete Selected Alarms
                            </button>
                        </div>
                    )}
                </section>
            </div>
            
            {/* Toast Container */}
            <ToastContainer
                position="bottom-right"
                autoClose={3000}
                hideProgressBar={false}
                newestOnTop
                closeOnClick
                rtl={false}
                pauseOnFocusLoss
                draggable
                pauseOnHover
                theme="colored"
            />
        </div>
    );
};

export default App;
