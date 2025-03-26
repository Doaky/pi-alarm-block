export interface Alarm {
    id: string;
    hour: number;
    minute: number;
    days: number[];
    is_primary_schedule: boolean;
    active: boolean;
}

export type ScheduleType = "a" | "b" | "off";
