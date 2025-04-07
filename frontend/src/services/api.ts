// Get API base URL from environment or default to localhost
const API_URL = import.meta.env.VITE_API_URL || window.location.protocol + '//' + window.location.hostname + ':8000';

import { Alarm, ScheduleType } from '../types/index';

export const fetchAlarms = async (): Promise<Alarm[]> => {
    const response = await fetch(`${API_URL}/api/v1/alarms`);
    if (!response.ok) {
        throw new Error('Failed to fetch alarms');
    }
    return response.json();
};

export const fetchSchedule = async (): Promise<{ schedule: ScheduleType }> => {
    const response = await fetch(`${API_URL}/api/v1/schedule`);
    if (!response.ok) {
        throw new Error('Failed to fetch schedule');
    }
    return response.json();
};

export const setSchedule = async (schedule: ScheduleType): Promise<void> => {
    const response = await fetch(`${API_URL}/api/v1/schedule`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ schedule }),
    });
    if (!response.ok) {
        throw new Error('Failed to set schedule');
    }
};

export const setAlarm = async (alarm: Omit<Alarm, 'active'>): Promise<{ alarm: Alarm }> => {
    const response = await fetch(`${API_URL}/api/v1/set-alarm`, {
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
    const response = await fetch(`${API_URL}/api/v1/play-alarm`, {
        method: "POST"
    });
    if (!response.ok) {
        throw new Error('Failed to play alarm');
    }
};

export const stopAlarm = async (): Promise<void> => {
    const response = await fetch(`${API_URL}/api/v1/stop-alarm`, {
        method: "POST"
    });
    if (!response.ok) {
        throw new Error('Failed to stop alarm');
    }
};

export const playWhiteNoise = async (): Promise<void> => {
    const response = await fetch(`${API_URL}/api/v1/white-noise`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "play" }),
    });
    if (!response.ok) {
        throw new Error('Failed to play white noise');
    }
};

export const stopWhiteNoise = async (): Promise<void> => {
    const response = await fetch(`${API_URL}/api/v1/white-noise`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "stop" }),
    });
    if (!response.ok) {
        throw new Error('Failed to stop white noise');
    }
};

export const adjustVolume = async (volume: number): Promise<void> => {
    const response = await fetch(`${API_URL}/api/v1/volume`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ volume }),
    });
    if (!response.ok) {
        throw new Error('Failed to adjust volume');
    }
};

export const getWhiteNoiseStatus = async (): Promise<{ is_playing: boolean, mode: string }> => {
    const response = await fetch(`${API_URL}/api/v1/white-noise/status`);
    if (!response.ok) {
        throw new Error('Failed to get white noise status');
    }
    return response.json();
};

export const getVolume = async (): Promise<{ volume: number, mode: string }> => {
    const response = await fetch(`${API_URL}/api/v1/volume`);
    if (!response.ok) {
        throw new Error('Failed to get volume level');
    }
    return response.json();
};

export const getAlarmStatus = async (): Promise<{ is_playing: boolean, mode: string }> => {
    const response = await fetch(`${API_URL}/api/v1/alarm/status`);
    if (!response.ok) {
        throw new Error('Failed to get alarm status');
    }
    return response.json();
};

export const shutdownSystem = async (): Promise<void> => {
    try {
        const response = await fetch(`${API_URL}/api/v1/shutdown`, {
            method: "POST"
        });
        if (!response.ok) {
            throw new Error('Failed to initiate shutdown');
        }
    } catch (error) {
        console.error('Shutdown error:', error);
        throw error;
    }
};
