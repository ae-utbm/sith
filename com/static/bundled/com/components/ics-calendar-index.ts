import { makeUrl } from "#core:utils/api";
import { inheritHtmlElement, registerComponent } from "#core:utils/web-components";
import { Calendar } from "@fullcalendar/core";
import enLocale from "@fullcalendar/core/locales/en-gb";
import frLocale from "@fullcalendar/core/locales/fr";
import dayGridPlugin from "@fullcalendar/daygrid";
import iCalendarPlugin from "@fullcalendar/icalendar";
import listPlugin from "@fullcalendar/list";
import { calendarCalendarExternal, calendarCalendarInternal } from "#openapi";

@registerComponent("ics-calendar")
export class IcsCalendar extends inheritHtmlElement("div") {
  static observedAttributes = ["locale"];
  private calendar: Calendar;
  private locale = "en";

  attributeChangedCallback(name: string, _oldValue?: string, newValue?: string) {
    if (name !== "locale") {
      return;
    }

    this.locale = newValue;
  }

  isMobile() {
    return window.innerWidth < 765;
  }

  currentView() {
    // Get view type based on viewport
    return this.isMobile() ? "listMonth" : "dayGridMonth";
  }

  currentToolbar() {
    if (this.isMobile()) {
      return {
        left: "prev,next",
        center: "title",
        right: "",
      };
    }
    return {
      left: "prev,next today",
      center: "title",
      right: "dayGridMonth,dayGridWeek,dayGridDay",
    };
  }

  async connectedCallback() {
    super.connectedCallback();
    this.calendar = new Calendar(this.node, {
      plugins: [dayGridPlugin, iCalendarPlugin, listPlugin],
      locales: [frLocale, enLocale],
      height: "auto",
      locale: this.locale,
      initialView: this.currentView(),
      headerToolbar: this.currentToolbar(),
      eventSources: [
        {
          url: await makeUrl(calendarCalendarInternal),
          format: "ics",
        },
        {
          url: await makeUrl(calendarCalendarExternal),
          format: "ics",
        },
      ],
      windowResize: () => {
        this.calendar.changeView(this.currentView());
        this.calendar.setOption("headerToolbar", this.currentToolbar());
      },
    });
    this.calendar.render();
  }
}
