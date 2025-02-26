import { useState, useEffect } from "react";

// Define the expected structure of an alarm
interface Alarm {
    hour: number;
    minute: number;
    days: number[];
}

const App = () => {
    const [alarms, setAlarms] = useState<Alarm[]>([]);

    useEffect(() => {
        fetch("/alarms")
            .then(res => res.json())
            .then((data: Alarm[]) => setAlarms(data));
    }, []);

    const setAlarm = () => {
        fetch("/alarms", {
            method: "POST",
            body: JSON.stringify({ hour: 7, minute: 30, days: [1,2,3,4,5] }),
            headers: { "Content-Type": "application/json" }
        });
    };

    return (
        <div>
            <h1>Alarm Manager</h1>
            <button onClick={setAlarm}>Set Alarm</button>
            <ul>
                {alarms.map((a, index) => (
                    <li key={index}>{a.hour}:{a.minute}</li>
                ))}
            </ul>
        </div>
    );
};

export default App;
