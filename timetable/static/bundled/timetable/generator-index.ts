import html2canvas from "html2canvas";

// see https://regex101.com/r/QHSaPM/2
const TIMETABLE_ROW_RE: RegExp =
  /^(?<ueCode>\w.+\w)\s+(?<courseType>[A-Z]{2}\d)\s+((?<weekGroup>[AB])\s+)?(?<weekday>(lundi)|(mardi)|(mercredi)|(jeudi)|(vendredi)|(samedi)|(dimanche))\s+(?<startHour>\d{2}:\d{2})\s+(?<endHour>\d{2}:\d{2})\s+[\dA-B]\s+((?<attendance>[\wé]*)\s+)?(?<room>\w+(?:, \w+)?)$/;

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
const SLOT_WIDTH = 250 as const; // Each weekday ha a width of 400px in the timetable
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
    endSlot: 0,
    table: {
      height: 0,
      width: 0,
    },

    colors: {} as Record<string, string>,
    colorPalette: [
      "#27ae60",
      "#2980b9",
      "#c0392b",
      "#7f8c8d",
      "#f1c40f",
      "#1abc9c",
      "#95a5a6",
      "#26C6DA",
      "#c2185b",
      "#e64a19",
      "#1b5e20",
    ],

    generate() {
      try {
        this.courses = parseSlots(this.content);
      } catch {
        this.error = gettext(
          "Wrong timetable format. Make sure you copied if from your student folder.",
        );
        return;
      }

      // color each UE
      let colorIndex = 0;
      for (const slot of this.courses) {
        if (!this.colors[slot.ueCode]) {
          this.colors[slot.ueCode] =
            this.colorPalette[colorIndex % this.colorPalette.length];
          colorIndex++;
        }
      }

      this.displayedWeekdays = WEEKDAYS.filter((day) =>
        this.courses.some((slot: TimetableSlot) => slot.weekday === day),
      );
      this.startSlot = this.courses.reduce(
        (acc: number, curr: TimetableSlot) => Math.min(acc, curr.startSlot),
        25 * 4,
      );
      this.endSlot = this.courses.reduce(
        (acc: number, curr: TimetableSlot) => Math.max(acc, curr.endSlot),
        1,
      );
      this.table.height = SLOT_HEIGHT * (this.endSlot - this.startSlot);
      this.table.width = SLOT_WIDTH * this.displayedWeekdays.length;
    },

    getStyle(slot: TimetableSlot) {
      const hasWeekGroup = slot.weekGroup !== undefined;
      const width = hasWeekGroup ? SLOT_WIDTH / 2 : SLOT_WIDTH;
      const leftOffset = slot.weekGroup === "B" ? SLOT_WIDTH / 2 : 0;
      return {
        height: `${(slot.endSlot - slot.startSlot) * SLOT_HEIGHT}px`,
        width: `${width}px`,
        top: `${(slot.startSlot - this.startSlot) * SLOT_HEIGHT}px`,
        left: `${this.displayedWeekdays.indexOf(slot.weekday) * SLOT_WIDTH + leftOffset}px`,
        backgroundColor: this.colors[slot.ueCode],
      };
    },

    getHours(): [string, object][] {
      let hour: number = Number.parseInt(
        this.courses
          .map((c: TimetableSlot) => c.startHour)
          .reduce((res: string, hour: string) => (hour < res ? hour : res), "24:00")
          .split(":")[0],
      );
      const res: [string, object][] = [];
      for (let i = 0; i <= this.endSlot - this.startSlot; i += 60 / MINUTES_PER_SLOT) {
        res.push([`${hour}:00`, { top: `${i * SLOT_HEIGHT}px` }]);
        hour += 1;
      }
      return res;
    },

    getWidth() {
      return this.displayedWeekdays.length * SLOT_WIDTH + 20;
    },

    async savePng() {
      const elem = document.getElementById("timetable");
      const img = (await html2canvas(elem)).toDataURL();
      const downloadLink = document.createElement("a");
      downloadLink.href = img;
      downloadLink.download = "edt.png";
      document.body.appendChild(downloadLink);
      downloadLink.click();
      downloadLink.remove();
    },
  }));
});
