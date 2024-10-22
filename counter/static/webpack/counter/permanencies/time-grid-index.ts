import { paginated } from "#core:utils/api";
import { exportToHtml } from "#core:utils/globals";
import { Calendar } from "@fullcalendar/core";
import timeGridPlugin from "@fullcalendar/timegrid";
import {
  type PermanencyFetchPermanenciesData,
  type PermanencySchema,
  permanencyFetchPermanencies,
} from "#openapi";

interface ActivityTimeGridConfig {
  canvas: HTMLCanvasElement;
  startDate: Date;
  counterId: number;
  locale: string;
}

interface OpeningTime {
  start: Date;
  end: Date;
}

interface EventInput {
  start: Date;
  end: Date;
  backgroundColor: string;
  title?: string;
}

exportToHtml("loadActivityTimeGrid", loadActivityTimeGrid);

async function loadActivityTimeGrid(options: ActivityTimeGridConfig) {
  const permanencies = await paginated(permanencyFetchPermanencies, {
    query: {
      counter: [options.counterId],
      // biome-ignore lint/style/useNamingConvention: backend API uses snake_case
      took_place_after: options.startDate.toISOString(),
    },
  } as PermanencyFetchPermanenciesData);

  const events = getEvents(permanencies);

  const calendar = new Calendar(options.canvas, {
    plugins: [timeGridPlugin],
    initialView: "timeGridWeek",
    locale: options.locale,
    dayHeaderFormat: { weekday: "long" },
    firstDay: 1,
    views: { timeGrid: { allDaySlot: false } },
    scrollTime: "09:00:00",
    headerToolbar: { left: "prev today", center: "title", right: "" },
    events: events,
    nowIndicator: true,
    height: 600,
  });
  calendar.render();

  calendar.on("datesSet", async (info) => {
    if (options.startDate <= info.start) {
      return;
    }
    const newPerms = await paginated(permanencyFetchPermanencies, {
      query: {
        counter: [options.counterId],
        // biome-ignore lint/style/useNamingConvention: backend API uses snake_case
        end_after: info.startStr,
        // biome-ignore lint/style/useNamingConvention: backend API uses snake_case
        start_before: info.endStr,
      },
    } as PermanencyFetchPermanenciesData);
    options.startDate = info.start;
    calendar.addEventSource(getEvents(newPerms, false));
    permanencies.push(...newPerms);
    calendar.render();
  });
}

function roundToQuarter(date: Date, ceil: boolean) {
  const result = date;
  const minutes = date.getMinutes();
  // removes minutes exceeding the lower quarter and adds 15 minutes if rounded to ceiling
  result.setMinutes(minutes - (minutes % 15) + +ceil * 15, 0, 0);
  return result;
}

function convertPermanencyToOpeningTime(permanency: PermanencySchema): OpeningTime {
  return {
    start: roundToQuarter(new Date(permanency.start), false),
    end: roundToQuarter(new Date(permanency.end ?? Date.now()), true),
  };
}

function getOpeningTimes(rawPermanencies: PermanencySchema[]) {
  const permanencies = rawPermanencies
    .map(convertPermanencyToOpeningTime)
    .sort((a, b) => a.start.getTime() - b.start.getTime());

  const openingTimes: OpeningTime[] = [];

  for (const permanency of permanencies) {
    // if there are no opening times, add the first one
    if (openingTimes.length === 0) {
      openingTimes.push(permanency);
    } else {
      const lastPermanency = openingTimes[openingTimes.length - 1];
      // if the new permanency starts before the 15 minutes following the end of the last one, merge them
      if (permanency.start <= lastPermanency.end) {
        lastPermanency.end = new Date(
          Math.max(lastPermanency.end.getTime(), permanency.end.getTime()),
        );
      } else {
        openingTimes.push(permanency);
      }
    }
  }
  return openingTimes;
}

function getEvents(permanencies: PermanencySchema[], currentWeek = true): EventInput[] {
  const openingTimes = getOpeningTimes(permanencies);
  const events: EventInput[] = [];
  for (const openingTime of openingTimes) {
    let shift = false;
    if (currentWeek) {
      const lastMonday = getLastMonday();
      shift = openingTime.end < lastMonday;
    }
    // if permanencies took place last week (=before monday),
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
function getLastMonday(now = new Date()): Date {
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
