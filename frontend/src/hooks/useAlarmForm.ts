import { useState } from 'react';
import { toast } from 'react-toastify';
import dayjs from 'dayjs';
import { setAlarm } from '../services/api';
import { Alarm } from '../types/index';

export const useAlarmForm = (onAlarmSet: (alarm: Alarm) => void) => {
    const [selectedTime, setSelectedTime] = useState<dayjs.Dayjs | null>(dayjs().hour(7).minute(30).second(0));
    const [days, setDays] = useState<number[]>([]);
    const [isPrimary, setIsPrimary] = useState(true);

    const handleSetAlarm = async () => {
        if (!selectedTime) {
            toast.warning("Please select a time");
            return;
        }

        if (days.length === 0) {
            toast.warning("Please select at least one day");
            return;
        }

        const newAlarm = {
            id: crypto.randomUUID(),
            hour: selectedTime.hour(),
            minute: selectedTime.minute(),
            days: [...days].sort(),
            is_primary_schedule: isPrimary,
            active: true,
        };

        try {
            const { alarm } = await setAlarm(newAlarm);
            onAlarmSet(alarm);
            toast.success("Alarm set successfully");
            
            // Reset form
            setDays([]);
            setSelectedTime(dayjs());
        } catch (err) {
            toast.error("Failed to set alarm");
            console.error("Error setting alarm:", err);
        }
    };

    return {
        selectedTime,
        setSelectedTime,
        days,
        setDays,
        isPrimary,
        setIsPrimary,
        handleSetAlarm
    };
};
