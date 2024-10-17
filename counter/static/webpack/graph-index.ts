import { paginated } from "#core:utils/api";
import { exportToHtml } from "#core:utils/globals";
import { Calendar } from "@fullcalendar/core";
import timeGridPlugin from "@fullcalendar/timegrid";
import {
  type PermanencyFetchPermananciesData,
  type PermanencySchema,
  permanencyFetchPermanancies,
} from "#openapi";

interface ActivityChartConfig {
  canvas: HTMLCanvasElement;
  startDate: Date;
  counterId: number;
}

interface OpeningTime {
  start: Date;
  end: Date;
}

interface EventInput {
  start: Date;
  end: Date;
  backgroundColor: string;
}

// TODO: Fix du look (bandes blanches dans la table, ...)
// TODO: Semaines passées

exportToHtml("loadChart", loadChart);

async function loadChart(options: ActivityChartConfig) {
  const permanancies = await paginated(permanencyFetchPermanancies, {
    query: {
      counter: [options.counterId],
      // biome-ignore lint/style/useNamingConvention: backend API uses snake_case
      start_date: options.startDate.toISOString(),
    },
  } as PermanencyFetchPermananciesData);

  const events = getEvents(permanancies);

  const calendar = new Calendar(options.canvas, {
    plugins: [timeGridPlugin],
    initialView: "timeGridWeek",
    locale: "fr",
    slotLabelFormat: { hour: "2-digit", minute: "2-digit", hour12: false },
    dayHeaderFormat: { weekday: "long" },
    firstDay: 1,
    views: { timeGrid: { allDaySlot: false } },
    scrollTime: "09:00:00",
    headerToolbar: { left: "", center: "", right: "" },
    events: events,
    nowIndicator: true,
    height: 600,
  });
  calendar.render();
}

function roundToQuarter(date: Date, ceil: boolean) {
  const result = date;
  const minutes = date.getMinutes();
  // removes minutes exceeding the lower quarter and adds 15 minutes if rounded to ceiling
  result.setMinutes(minutes + +ceil * 15 - (minutes % 15), 0, 0);
  return result;
}

function convertPermanancyToOpeningTime(permanancy: PermanencySchema): OpeningTime {
  return {
    start: roundToQuarter(new Date(permanancy.start), false),
    end: roundToQuarter(new Date(permanancy.end ?? Date.now()), true),
  };
}

function getOpeningTimes(rawPermanancies: PermanencySchema[]) {
  const permanancies = rawPermanancies
    .map(convertPermanancyToOpeningTime)
    .sort((a, b) => a.start.getTime() - b.start.getTime());

  const openingTimes: OpeningTime[] = [];

  for (const permanancy of permanancies) {
    // if there are no opening times, add the first one
    if (openingTimes.length === 0) {
      openingTimes.push(permanancy);
    } else {
      const lastPermanancy = openingTimes[openingTimes.length - 1];
      // if the new permanancy starts before the 15 minutes following the end of the last one, merge them
      if (permanancy.start <= lastPermanancy.end) {
        lastPermanancy.end = new Date(
          Math.max(lastPermanancy.end.getTime(), permanancy.end.getTime()),
        );
      } else {
        openingTimes.push(permanancy);
      }
    }
  }
  return openingTimes;
}

function getEvents(permanancies: PermanencySchema[]) {
  const openingTimes = getOpeningTimes(permanancies);
  const events: EventInput[] = [];
  for (const openingTime of openingTimes) {
    const lastMonday = getLastMonday();
    const shift = openingTime.end < lastMonday;
    // if permanancies took place last week (=before monday),
    // -> display them in lightblue as part of the current week
    events.push({
      start: shift ? shiftDateByDays(openingTime.start, 7) : openingTime.start,
      end: shift ? shiftDateByDays(openingTime.end, 7) : openingTime.end,
      backgroundColor: shift ? "lightblue" : "green",
    });
  }
  return events;
}

// Function to get last Monday at 00:00
function getLastMonday(): Date {
  const now = new Date();
  const dayOfWeek = now.getDay();
  const lastMonday = new Date(now);
  lastMonday.setDate(now.getDate() - ((dayOfWeek + 6) % 7)); // Adjust for Monday as day 1
  lastMonday.setHours(0, 0, 0, 0);
  return lastMonday;
}

function shiftDateByDays(date: Date, days: number): Date {
  const newDate = new Date(date);
  newDate.setDate(date.getDate() + days);
  return newDate;
}
