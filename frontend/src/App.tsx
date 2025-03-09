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
      .then((res) => res.json())
      .then((data: Alarm[]) => setAlarms(data));
  }, []);

  const setAlarm = () => {
    fetch("/alarms", {
      method: "POST",
      body: JSON.stringify({ hour: 7, minute: 30, days: [1, 2, 3, 4, 5] }),
      headers: { "Content-Type": "application/json" },
    });
  };

  return (
    <div class="dm-container">
      <h1>Device Manager</h1>
      <div class="button-group">
        <button onClick={setAlarm}>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="1.5"
            stroke="currentColor"
            class="button-icon"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0M3.124 7.5A8.969 8.969 0 0 1 5.292 3m13.416 0a8.969 8.969 0 0 1 2.168 4.5"
            />
          </svg>
          Set Alarm
        </button>
        <ul>
          {alarms.map((a, index) => (
            <li key={index}>
              {a.hour}:{a.minute}
            </li>
          ))}
        </ul>
        <button>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="1.5"
            stroke="currentColor"
            class="button-icon"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M19.114 5.636a9 9 0 0 1 0 12.728M16.463 8.288a5.25 5.25 0 0 1 0 7.424M6.75 8.25l4.72-4.72a.75.75 0 0 1 1.28.53v15.88a.75.75 0 0 1-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.009 9.009 0 0 1 2.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75Z"
            />
          </svg>
          White Noise
        </button>
      </div>
    </div>
  );
};

export default App;
