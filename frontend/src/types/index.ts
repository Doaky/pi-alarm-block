export interface Alarm {
    id: string;
    hour: number;
    minute: number;
    days: number[];
    schedule: string;
    active: boolean;
}

export type ScheduleType = "a" | "b" | "off";
