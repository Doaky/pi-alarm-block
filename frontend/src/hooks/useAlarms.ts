import { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { Alarm, ScheduleType } from '../types/index';
import { fetchAlarms, fetchSchedule } from '../services/api';

export const useAlarms = () => {
    const [alarms, setAlarms] = useState<Alarm[]>([]);
    const [selectedAlarms, setSelectedAlarms] = useState<Set<string>>(new Set());
    const [currentSchedule, setCurrentSchedule] = useState<ScheduleType>("a");
    const [isLoading, setIsLoading] = useState(true);

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
