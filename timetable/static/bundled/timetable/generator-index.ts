// see https://regex101.com/r/QHSaPM/2
const TIMETABLE_ROW_RE: RegExp =
  /^(?<ueCode>[A-Z\d]{4}(?:\+[A-Z\d]{4})?)\s+(?<courseType>[A-Z]{2}\d)\s+((?<weekGroup>[AB])\s+)?(?<weekday>(lundi)|(mardi)|(mercredi)|(jeudi)|(vendredi)|(samedi)|(dimanche))\s+(?<startHour>\d{2}:\d{2})\s+(?<endHour>\d{2}:\d{2})\s+[\dA-B]\s+(?:[\wé]*\s+)?(?<room>\w+(?:, \w+)?)$/;

const DEFAULT_TIMETABLE: string = `DS52\t\tCM1\t\tlundi\t08:00\t10:00\t1\tPrésentiel\tA113
DS53\t\tCM1\t\tlundi\t10:15\t12:15\t1\tPrésentiel\tA101
DS53\t\tTP1\t\tlundi\t13:00\t16:00\t1\tPrésentiel\tH010
SO03\t\tCM1\t\tlundi\t16:15\t17:45\t1\tPrésentiel\tA103
SO03\t\tTD1\t\tlundi\t17:45\t19:45\t1\tPrésentiel\tA103
DS50\t\tTP1\t\tmardi\t08:00\t10:00\t1\tPrésentiel\tA216
DS51\t\tCM1\t\tmardi\t10:15\t12:15\t1\tPrésentiel\tA216
DS51\t\tTP1\t\tmardi\t14:00\t18:00\t1\tPrésentiel\tH010
DS52\t\tTP2\tA\tjeudi\t08:00\t10:00\tA\tPrésentiel\tA110a, A110b
DS52\t\tTD1\t\tjeudi\t10:15\t12:15\t1\tPrésentiel\tA110a, A110b
LC02\t\tTP1\t\tjeudi\t15:00\t16:00\t1\tPrésentiel\tA209
LC02\t\tTD1\t\tjeudi\t16:15\t18:15\t1\tPrésentiel\tA206`;

type WeekDay =
  | "lundi"
  | "mardi"
  | "mercredi"
  | "jeudi"
  | "vendredi"
  | "samedi"
  | "dimanche";

const WEEKDAYS = [
  "lundi",
  "mardi",
  "mercredi",
  "jeudi",
  "vendredi",
  "samedi",
  "dimanche",
] as const;

const SLOT_HEIGHT = 20 as const; // Each 15min has a height of 20px in the timetable
const SLOT_WIDTH = 400 as const; // Each weekday ha a width of 400px in the timetable
const MINUTES_PER_SLOT = 15 as const;

interface TimetableSlot {
  courseType: string;
  room: string;
  startHour: string;
  endHour: string;
  startSlot: number;
  endSlot: number;
  ueCode: string;
  weekGroup?: string;
  weekday: WeekDay;
}

function parseSlots(s: string): TimetableSlot[] {
  return s
    .split("\n")
    .filter((s: string) => s.length > 0)
    .map((row: string) => {
      const parsed = TIMETABLE_ROW_RE.exec(row);
      if (!parsed) {
        throw new Error(`Couldn't parse row ${row}`);
      }
      const [startHour, startMin] = parsed.groups.startHour
        .split(":")
        .map((i) => Number.parseInt(i));
      const [endHour, endMin] = parsed.groups.endHour
        .split(":")
        .map((i) => Number.parseInt(i));
      return {
        ...parsed.groups,
        startSlot: Math.floor((startHour * 60 + startMin) / MINUTES_PER_SLOT),
        endSlot: Math.floor((endHour * 60 + endMin) / MINUTES_PER_SLOT),
      } as unknown as TimetableSlot;
    });
}

document.addEventListener("alpine:init", () => {
  Alpine.data("timetableGenerator", () => ({
    content: DEFAULT_TIMETABLE,
    error: "",
    displayedWeekdays: [] as WeekDay[],
    courses: [] as TimetableSlot[],
    startSlot: 0,
    table: {
      height: 0,
      width: 0,
    },

    generate() {
      try {
        this.courses = parseSlots(this.content);
      } catch {
        this.error = gettext(
          "Wrong timetable format. Make sure you copied if from your student folder.",
        );
        return;
      }
      this.displayedWeekdays = WEEKDAYS.filter((day) =>
        this.courses.some((slot: TimetableSlot) => slot.weekday === day),
      );
      this.startSlot = this.courses.reduce(
        (acc: number, curr: TimetableSlot) => Math.min(acc, curr.startSlot),
        24 * 4,
      );
      this.endSlot = this.courses.reduce(
        (acc: number, curr: TimetableSlot) => Math.max(acc, curr.endSlot),
        0,
      );
      this.table.height = SLOT_HEIGHT * (this.endSlot - this.startSlot);
      this.table.width = SLOT_WIDTH * this.displayedWeekdays.length;
    },

    getStyle(slot: TimetableSlot) {
      return {
        height: `${(slot.endSlot - slot.startSlot) * SLOT_HEIGHT}px`,
        width: `${SLOT_WIDTH}px`,
        top: `${(slot.startSlot - this.startSlot) * SLOT_HEIGHT}px`,
        left: `${this.displayedWeekdays.indexOf(slot.weekday) * SLOT_WIDTH}px`,
      };
    },
  }));
});
