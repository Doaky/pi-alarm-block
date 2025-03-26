import { useState, useEffect } from "react";
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { createTheme } from '@mui/material/styles';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs from 'dayjs';
import './styles.css';
import { ScheduleControls } from './components/ScheduleControls';
import { AlarmForm } from './components/AlarmForm';
import { AlarmList } from './components/AlarmList';
import { AudioControls } from './components/AudioControls';
import { Alarm, ScheduleType } from './types/index';

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

    return (
        <LocalizationProvider dateAdapter={AdapterDayjs}>
            <div className="min-h-screen p-4 bg-gray-900 text-white body-font">
                <div className="max-w-4xl mx-auto">
                    <div className="mb-8">
                        <h1 className="text-3xl font-bold title-font">Alarm Block</h1>
                    </div>

                    <ScheduleControls
                        currentSchedule={currentSchedule}
                        setCurrentSchedule={setCurrentSchedule}
                    />

                    <AlarmForm
                        selectedTime={selectedTime}
                        setSelectedTime={setSelectedTime}
                        days={days}
                        setDays={setDays}
                        isPrimary={isPrimary}
                        setIsPrimary={setIsPrimary}
                        setAlarms={setAlarms}
                        darkTheme={darkTheme}
                    />

                    {!isLoading && (
                        <AlarmList
                            alarms={alarms}
                            setAlarms={setAlarms}
                            selectedAlarms={selectedAlarms}
                            setSelectedAlarms={setSelectedAlarms}
                        />
                    )}

                    <AudioControls
                        isPlaying={isPlaying}
                        setIsPlaying={setIsPlaying}
                        isWhiteNoiseActive={isWhiteNoiseActive}
                        setIsWhiteNoiseActive={setIsWhiteNoiseActive}
                    />
                </div>
                <ToastContainer position="bottom-right" theme="dark" />
            </div>
        </LocalizationProvider>
    );
};

export default App;
