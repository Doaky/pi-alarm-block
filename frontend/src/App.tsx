import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { createTheme } from '@mui/material/styles';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import './styles.css';
import { ScheduleControls } from './components/ScheduleControls';
import { AlarmForm } from './components/AlarmForm';
import { AlarmList } from './components/AlarmList';
import { AudioControls } from './components/AudioControls';
import { useAlarms } from './hooks/useAlarms';
import { useAlarmForm } from './hooks/useAlarmForm';
import { useAudio } from './hooks/useAudio';

const darkTheme = createTheme({
    palette: {
        mode: 'dark',
    },
});

const App = () => {
    // Custom hooks for state management
    const {
        alarms,
        setAlarms,
        selectedAlarms,
        setSelectedAlarms,
        currentSchedule,
        setCurrentSchedule,
        isLoading
    } = useAlarms();

    const {
        selectedTime,
        setSelectedTime,
        days,
        setDays,
        isPrimary,
        setIsPrimary,
        handleSetAlarm
    } = useAlarmForm((newAlarm) => setAlarms(prev => [...prev, newAlarm]));

    const {
        isPlaying,
        setIsPlaying,
        isWhiteNoiseActive,
        setIsWhiteNoiseActive,
        isLoading: audioLoading,
        volume,
        handleVolumeChange
    } = useAudio();

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
                        handleSetAlarm={handleSetAlarm}
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

                    {!audioLoading && (
                        <AudioControls
                            isPlaying={isPlaying}
                            setIsPlaying={setIsPlaying}
                            isWhiteNoiseActive={isWhiteNoiseActive}
                            setIsWhiteNoiseActive={setIsWhiteNoiseActive}
                            volume={volume}
                            handleVolumeChange={handleVolumeChange}
                        />
                    )}
                </div>
                <ToastContainer 
                    position="top-center" 
                    theme="dark" 
                    limit={3} 
                    newestOnTop 
                />
            </div>
        </LocalizationProvider>
    );
};

export default App;
