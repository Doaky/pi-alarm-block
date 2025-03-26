import { FC, Dispatch, SetStateAction } from 'react';
import { toast } from 'react-toastify';
import { Divider } from '@mui/material';
import { Alarm } from '../types/index';

const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"] as const;

interface AlarmListProps {
    alarms: Alarm[];
    setAlarms: Dispatch<SetStateAction<Alarm[]>>;
    selectedAlarms: Set<string>;
    setSelectedAlarms: Dispatch<SetStateAction<Set<string>>>;
}

export const AlarmList: FC<AlarmListProps> = ({ 
    alarms, 
    setAlarms, 
    selectedAlarms, 
    setSelectedAlarms 
}) => {
    const formatTime = (hour: number, minute: number): string => {
        const period = hour >= 12 ? 'PM' : 'AM';
        const displayHour = hour % 12 || 12;
        return `${displayHour}:${minute.toString().padStart(2, '0')} ${period}`;
    };

    const toggleAlarmSelection = (alarmId: string) => {
        setSelectedAlarms((prev) => {
            const newSet = new Set(prev);
            if (newSet.has(alarmId)) {
                newSet.delete(alarmId);
            } else {
                newSet.add(alarmId);
            }
            return newSet;
        });
    };

    const toggleAlarmActive = async (alarm: Alarm) => {
        const updatedAlarm = { ...alarm, active: !alarm.active };
        try {
            const response = await fetch("/set-alarm", {
                method: "PUT",
                body: JSON.stringify(updatedAlarm),
                headers: { "Content-Type": "application/json" }
            });
            
            if (!response.ok) throw new Error("Failed to update alarm");
            
            setAlarms((prev) => prev.map((a) => a.id === alarm.id ? updatedAlarm : a));
            toast.success(`Alarm ${updatedAlarm.active ? "activated" : "deactivated"}`);
        } catch (err) {
            toast.error("Failed to update alarm");
            console.error("Error updating alarm:", err);
        }
    };

    const handleDeleteSelectedAlarms = async () => {
        const alarmIds = Array.from(selectedAlarms);

        if (alarmIds.length === 0) {
            toast.warning("Please select alarms to delete");
            return;
        }

        try {
            const response = await fetch("/alarms", {
                method: "DELETE",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(alarmIds),
            });
            
            if (!response.ok) throw new Error("Failed to delete alarms");
            
            setAlarms((prev) => prev.filter((alarm) => !alarmIds.includes(alarm.id)));
            setSelectedAlarms(new Set());
            toast.success("Selected alarms deleted");
        } catch (err) {
            toast.error("Failed to delete alarms");
            console.error("Error deleting alarms:", err);
        }
    };

    // Sort alarms by time and schedule
    const sortedAlarms = [...alarms].sort((a, b) => {
        if (a.is_primary_schedule !== b.is_primary_schedule) {
            return a.is_primary_schedule ? -1 : 1;
        }
        return a.hour * 60 + a.minute - (b.hour * 60 + b.minute);
    });

    return (
        <div className="mb-8 p-4 bg-gray-800 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4 title-font">Alarms</h2>
            {sortedAlarms.length === 0 ? (
                <p>No alarms set</p>
            ) : (
                <div className="space-y-2">
                    {sortedAlarms.map((alarm, index) => {
                        const showDivider = index > 0 && alarm.is_primary_schedule !== sortedAlarms[index - 1].is_primary_schedule;
                        return (
                            <div key={alarm.id}>
                                {showDivider && <Divider className="my-4 border-gray-600" />}
                                <div
                                    className={`alarm-entry ${selectedAlarms.has(alarm.id) ? 'selected' : ''}`}
                                    onClick={() => toggleAlarmSelection(alarm.id)}
                                >
                                    <div className="flex justify-between items-center">
                                        <div>
                                            <span className="font-semibold">
                                                {formatTime(alarm.hour, alarm.minute)}
                                            </span>
                                            <span className="ml-4">
                                                {alarm.days.map((d: number) => DAYS[d]).join(', ')}
                                            </span>
                                        </div>
                                        <div className="flex items-center gap-4">
                                            <span className={`px-2 py-1 rounded ${
                                                alarm.is_primary_schedule
                                                    ? 'bg-blue-500 text-white'
                                                    : 'bg-purple-500 text-white'
                                            }`}>
                                                {alarm.is_primary_schedule ? 'Primary' : 'Secondary'}
                                            </span>
                                            <div
                                                className={`status-chip ${alarm.active ? 'active' : 'inactive'}`}
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    toggleAlarmActive(alarm);
                                                }}
                                            >
                                                {alarm.active ? 'Active' : 'Inactive'}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                    <button
                        onClick={handleDeleteSelectedAlarms}
                        className="w-full mt-4 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed"
                        disabled={selectedAlarms.size === 0}
                    >
                        Delete {selectedAlarms.size > 1 ? "Alarms" : "Alarm"}
                    </button>
                </div>
            )}
        </div>
    );
};
