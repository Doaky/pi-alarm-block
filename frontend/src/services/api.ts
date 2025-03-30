import { Alarm, ScheduleType } from '../types/index';

const API_BASE = '/api/v1';

export const fetchAlarms = async (): Promise<Alarm[]> => {
    const response = await fetch(`${API_BASE}/alarms`);
    if (!response.ok) {
        throw new Error('Failed to fetch alarms');
    }
    return response.json();
};

export const fetchSchedule = async (): Promise<{ schedule: ScheduleType }> => {
    const response = await fetch(`${API_BASE}/schedule/current`);
    if (!response.ok) {
        throw new Error('Failed to fetch schedule');
    }
    return response.json();
};

export const setAlarm = async (alarm: Omit<Alarm, 'active'>): Promise<{ alarm: Alarm }> => {
    const response = await fetch(`${API_BASE}/alarms`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(alarm),
    });
    if (!response.ok) {
        throw new Error('Failed to set alarm');
    }
    return response.json();
};
