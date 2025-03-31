// Get API base URL from environment or default to localhost
const API_URL = import.meta.env.VITE_API_URL || window.location.protocol + '//' + window.location.hostname + ':8000';
const API_BASE = `${API_URL}/api/v1`;

import { Alarm, ScheduleType } from '../types/index';

export const fetchAlarms = async (): Promise<Alarm[]> => {
    const response = await fetch(`${API_BASE}/alarms`);
    if (!response.ok) {
        throw new Error('Failed to fetch alarms');
    }
    return response.json();
};

export const fetchSchedule = async (): Promise<{ schedule: ScheduleType }> => {
    const response = await fetch(`${API_BASE}/schedule`);
    if (!response.ok) {
        throw new Error('Failed to fetch schedule');
    }
    return response.json();
};

export const setSchedule = async (schedule: ScheduleType): Promise<void> => {
    const response = await fetch(`${API_BASE}/schedule`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ schedule }),
    });
    if (!response.ok) {
        throw new Error('Failed to set schedule');
    }
};

export const setAlarm = async (alarm: Omit<Alarm, 'active'>): Promise<{ alarm: Alarm }> => {
    const response = await fetch(`${API_BASE}/set-alarm`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(alarm),
    });
    if (!response.ok) {
        throw new Error('Failed to set alarm');
    }
    return response.json();
};

export const playAlarm = async (): Promise<void> => {
    const response = await fetch(`${API_BASE}/play-alarm`, {
        method: "POST"
    });
    if (!response.ok) {
        throw new Error('Failed to play alarm');
    }
};

export const stopAlarm = async (): Promise<void> => {
    const response = await fetch(`${API_BASE}/stop-alarm`, {
        method: "POST"
    });
    if (!response.ok) {
        throw new Error('Failed to stop alarm');
    }
};

export const playWhiteNoise = async (): Promise<void> => {
    const response = await fetch(`${API_BASE}/white-noise`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "play" }),
    });
    if (!response.ok) {
        throw new Error('Failed to play white noise');
    }
};

export const stopWhiteNoise = async (): Promise<void> => {
    const response = await fetch(`${API_BASE}/white-noise`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "stop" }),
    });
    if (!response.ok) {
        throw new Error('Failed to stop white noise');
    }
};

export const adjustVolume = async (volume: number): Promise<void> => {
    const response = await fetch(`${API_BASE}/volume`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ volume }),
    });
    if (!response.ok) {
        throw new Error('Failed to adjust volume');
    }
};
