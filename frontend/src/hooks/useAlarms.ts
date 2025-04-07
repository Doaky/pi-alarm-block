import { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { Alarm, ScheduleType } from '../types';
import { fetchAlarms, fetchSchedule } from '../services/api';
import useWebSocket from './useWebSocket';

export const useAlarms = () => {
    const [alarms, setAlarms] = useState<Alarm[]>([]);
    const [selectedAlarms, setSelectedAlarms] = useState<Set<string>>(new Set());
    const [currentSchedule, setCurrentSchedule] = useState<ScheduleType>("a");
    const [isLoading, setIsLoading] = useState(true);

    // Setup WebSocket listeners for real-time updates
    useWebSocket({
        onAlarmUpdate: (updatedAlarms) => {
            setAlarms(updatedAlarms);
            console.log('Alarms updated via WebSocket');
        },
        onScheduleUpdate: (schedule: string) => {
            // Convert string to schedule type
            const newSchedule = schedule as ScheduleType;
            setCurrentSchedule(newSchedule);
            console.log(`Schedule updated to ${newSchedule} via WebSocket`);
        },
        onShutdown: () => {
            console.log('System shutdown notification received');
            // The WebSocket service will handle displaying the shutdown screen
        }
    });

    useEffect(() => {
        const loadData = async () => {
            try {
                const [alarmsData, scheduleData] = await Promise.all([
                    fetchAlarms(),
                    fetchSchedule()
                ]);
                setAlarms(alarmsData);
                setCurrentSchedule(scheduleData.schedule);
            } catch (error) {
                toast.error("Failed to load data");
                console.error("Error loading data:", error);
            } finally {
                setIsLoading(false);
            }
        };

        loadData();
    }, []);

    return {
        alarms,
        setAlarms,
        selectedAlarms,
        setSelectedAlarms,
        currentSchedule,
        setCurrentSchedule,
        isLoading
    };
};
