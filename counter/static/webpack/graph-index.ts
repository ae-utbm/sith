import { paginated } from "#core:utils/api";
import { exportToHtml } from "#core:utils/globals";
import {
  type PermanencyFetchPermananciesData,
  type PermanencySchema,
  permanencyFetchPermanancies,
} from "#openapi";

import { Calendar } from "@fullcalendar/core";
import timeGridPlugin from "@fullcalendar/timegrid";

interface ActivityChartConfig {
  canvas: HTMLCanvasElement;
  startDate: Date;
  counterId: number;
}

interface OpeningTime {
  start: Date;
  end: Date;
}

exportToHtml("loadChart", loadChart);

async function loadChart(options: ActivityChartConfig) {
  const permanancies = await paginated(permanencyFetchPermanancies, {
    query: {
      counter: [options.counterId],
      // biome-ignore lint/style/useNamingConvention: backend API uses snake_case
      start_date: options.startDate.toString(),
    },
  } as PermanencyFetchPermananciesData);

  const events = getEvents(permanancies);

  const calendar = new Calendar(options.canvas, {
    plugins: [timeGridPlugin],
    initialView: "timeGridWeek",
    locale: "fr",
    slotLabelFormat: {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    },
    dayHeaderFormat: {
      weekday: "long",
    },
    firstDay: 1,
    views: {
      timeGrid: {
        allDaySlot: false,
      },
    },
    scrollTime: "09:00:00",
    headerToolbar: {
      left: "",
      center: "",
      right: "",
    },
    //weekends: false,
    events: events,
    nowIndicator: true,
    //slotDuration: "00:15:00",
    height: 600,
  });
  calendar.render();
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
      if (
        // if the new permanancy starts before the 15 minutes following the end of the last one, merge them
        new Date(permanancy.start).setMinutes(permanancy.start.getMinutes() - 15) <
        lastPermanancy.end.getTime()
      ) {
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

function convertPermanancyToOpeningTime(permanancy: PermanencySchema): OpeningTime {
  return {
    start: new Date(permanancy.start),
    end: permanancy.end ? new Date(permanancy.end) : new Date(),
  };
}

function getEvents(permanancies: PermanencySchema[]) {
  const openingTimes = getOpeningTimes(permanancies);
  const events = [];
  for (const openingTime of openingTimes) {
    const lastMonday: Date = new Date();
    lastMonday.setDate(new Date().getDate() - ((new Date().getDay() - 1) % 7));
    lastMonday.setHours(0, 0, 0);

    // if permanancies took place before monday (last week), display them in lightblue as part of the current week
    if (openingTime.end < lastMonday) {
      events.push({
        start: new Date(openingTime.start).setDate(openingTime.start.getDate() + 7),
        end: new Date(openingTime.end).setDate(openingTime.end.getDate() + 7),
        backgroundColor: "lightblue",
      });
    } else {
      events.push({
        start: openingTime.start,
        end: openingTime.end,
        backgroundColor: "green",
      });
    }
  }
  //const openingTimesByDay = splitByDay(openingTimes);
  return events;
}
