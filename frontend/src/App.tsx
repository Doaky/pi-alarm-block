import { useState, useEffect } from "react";

// Define the expected structure of an alarm
interface Alarm {
    id: string;
    hour: number;
    minute: number;
    days: number[];
    is_primary_schedule: boolean;
    active: boolean;
}

const App = () => {
    const [alarms, setAlarms] = useState<Alarm[]>([]);

    // State for form inputs
    const [hour, setHour] = useState(7);
    const [minute, setMinute] = useState(30);
    const [days, setDays] = useState<number[]>([]);
    const [isPrimary, setIsPrimary] = useState(true);
    const [active, setActive] = useState(true);

    const [isPrimarySchedule, setIsPrimarySchedule] = useState(true);

    // States for toggling schedule and global status
    const [globalStatus, setGlobalStatus] = useState(true);

    // States for checking selected alarms to delete
    const [selectedAlarms, setSelectedAlarms] = useState<Set<string>>(new Set());

    useEffect(() => {
        // Fetch alarms
        fetch("/alarms")
            .then(res => res.json())
            .then((data: Alarm[]) => setAlarms(data))
            .catch(err => console.error("Error fetching alarms:", err));

        // Fetch initial schedule state
        fetch("/get_schedule")
            .then((res) => res.json())
            .then((data) => setIsPrimary(data.is_primary_schedule))
            .catch(err => {
                setIsPrimary(true); console.error("Error fetching schedule:", err)
            });

        // Fetch initial global status
        fetch("/get_global_status")
            .then((res) => res.json())
            .then((data) => setGlobalStatus(data.is_global_on))
            .catch(err => {
                setGlobalStatus(true); console.error("Error fetching global status:", err)
            });
    }, []);

    // Function to toggle day selection
    const toggleDay = (day: number) => {
        setDays(prev => 
            prev.includes(day) ? prev.filter(d => d !== day) : [...prev, day]
        );
    };

    // Function to set an alarm
    const handleSetAlarm = (e: React.FormEvent) => {
        e.preventDefault();

        // Validation: At least one day must be selected
        if (days.length === 0) {
            alert("Please select at least one day.");
            return;
        }

        const newAlarm = {
            id: crypto.randomUUID(), // Generate unique ID
            hour,
            minute,
            days: [...days].sort((a, b) => a - b),
            is_primary_schedule: isPrimary,
            active,
        };

        fetch("/set-alarm", {
            method: "PUT",
            body: JSON.stringify(newAlarm),
            headers: { "Content-Type": "application/json" }
        })
        .then(res => res.json())
        .then(data => {
            console.log(data);
            setAlarms([...alarms, data.alarm]);
        })
        .catch(err => console.error("Error setting alarm:", err));
    };

    // Function to toggle global status
    const handleGlobalStatusChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const newStatus = e.target.checked;
        setGlobalStatus(newStatus);

        fetch("/set_global_status", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ is_global_on: newStatus }),
        });
    };

    // Function to toggle schedule (primary/secondary)
    const handleScheduleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const newSchedule = e.target.value === "primary";
        setIsPrimarySchedule(newSchedule);

        fetch("/set_schedule", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ is_primary: newSchedule }),
        });
    };

    // Function to handle alarm selection for deletion
    const toggleAlarmSelection = (alarmId: string) => {
        setSelectedAlarms((prev) =>
            prev.has(alarmId) ? new Set([...prev].filter((id) => id !== alarmId)) : new Set(prev.add(alarmId))
        );
    };

    // Function to delete selected alarms
    const handleDeleteSelectedAlarms = () => {
        const alarmIds = Array.from(selectedAlarms);

        if (alarmIds.length === 0) {
            alert("Please select alarms to delete.");
            return;
        }

        fetch("/alarms", {
            method: "DELETE",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ alarm_ids: alarmIds }),
        })
        .then((res) => res.json())
        .then((data) => {
            console.log(data);
            setAlarms(alarms.filter((alarm) => !alarmIds.includes(alarm.id)));
            setSelectedAlarms(new Set()); // Clear selection after deletion
        })
        .catch((err) => console.error("Error deleting alarms:", err));
    };

    const playAlarm = () => {
        fetch("/play-alarm", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });
    };

    const stopAlarm = () => {
        fetch("/stop-alarm", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });
    };

    return (
        <div>
            <h1>Settings</h1>
            <div>
                <label>Primary Schedule:</label>
                <label>
                    <input
                    type="radio"
                    name="global_schedule"
                    value="primary"
                    checked={isPrimarySchedule}
                    onChange={handleScheduleChange}
                    />
                    Primary
                </label>
                <label>
                    <input
                    type="radio"
                    name="global_schedule"
                    value="secondary"
                    checked={!isPrimarySchedule}
                    onChange={handleScheduleChange}
                    />
                    Secondary
                </label>
            </div>

            <div>
                <label>
                <input
                    type="checkbox"
                    checked={globalStatus}
                    onChange={handleGlobalStatusChange}
                />
                Global Status: {globalStatus ? "Enabled" : "Disabled"}
                </label>
            </div>
            <button onClick={playAlarm}>Play Alarm</button>
            <button onClick={stopAlarm}>Stop Alarm</button>

            <h1>Alarm Manager</h1>
            {/* Alarm Input Form */}
            <form onSubmit={handleSetAlarm}>
                <div>
                    <label>Time: </label>
                    <input 
                        type="number" 
                        value={hour} 
                        onChange={(e) => setHour(parseInt(e.target.value))} 
                        min="0" max="23" 
                    />
                    :
                    <input 
                        type="number" 
                        value={minute} 
                        onChange={(e) => setMinute(parseInt(e.target.value))} 
                        min="0" max="59" 
                    />
                </div>

                <div>
                    <label>Days: </label>
                    {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day, index) => (
                        <label key={index}>
                            <input
                                type="checkbox"
                                checked={days.includes(index)}
                                onChange={() => toggleDay(index)}
                            />
                            {day}
                        </label>
                    ))}
                </div>

                <div>
                    <label>Primary Schedule: </label>
                    <label>
                        <input
                            type="radio"
                            name="schedule"
                            checked={isPrimary}
                            onChange={() => setIsPrimary(true)}
                        /> Primary
                    </label>
                    <label>
                        <input
                            type="radio"
                            name="schedule"
                            checked={!isPrimary}
                            onChange={() => setIsPrimary(false)}
                        /> Secondary
                    </label>
                </div>

                <div>
                    <label>Active: </label>
                    <input
                        type="checkbox"
                        checked={active}
                        onChange={() => setActive(prev => !prev)}
                    />
                </div>

                <button type="submit">Set Alarm</button>
            </form>

            <h1>Alarm List</h1>
            {alarms.length === 0 ? (
                <p>No alarms set</p>
            ) : (
                <div>
                <ul>
                    {alarms && alarms.map && alarms.map((alarm) => (
                    <li key={alarm.id}>
                        <input
                        type="checkbox"
                        checked={selectedAlarms.has(alarm.id)}
                        onChange={() => toggleAlarmSelection(alarm.id)}
                        />
                        {alarm.hour}:{alarm.minute.toString().padStart(2, "0")} - Days: {alarm.days.join(", ")}
                    </li>
                    ))}
                </ul>
                <button onClick={handleDeleteSelectedAlarms}>Delete Selected Alarms</button>
                </div>
            )}
        </div>
    );
};

export default App;
