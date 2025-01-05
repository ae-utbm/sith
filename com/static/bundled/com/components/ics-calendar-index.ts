import { makeUrl } from "#core:utils/api";
import { inheritHtmlElement, registerComponent } from "#core:utils/web-components";
import { Calendar, type EventClickArg } from "@fullcalendar/core";
import type { EventImpl } from "@fullcalendar/core/internal";
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

  formatDate(date: Date) {
    return new Intl.DateTimeFormat(this.locale, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(date);
  }

  createEventDetailPopup(event: EventClickArg) {
    // Delete previous popup
    const oldPopup = document.getElementById("event-details");
    if (oldPopup !== null) {
      oldPopup.remove();
    }

    const makePopupInfo = (info: HTMLElement, iconClass: string) => {
      const row = document.createElement("div");
      const icon = document.createElement("i");

      row.setAttribute("class", "event-details-row");

      icon.setAttribute("class", `event-detail-row-icon fa-xl ${iconClass}`);

      row.appendChild(icon);
      row.appendChild(info);

      return row;
    };

    const makePopupTitle = (event: EventImpl) => {
      const row = document.createElement("div");
      row.innerHTML = `
        <h4 class="event-details-row-content">
          ${event.title}
        </h4>
        <span class="event-details-row-content">
          ${this.formatDate(event.start)} - ${this.formatDate(event.end)}
        </span>
      `;
      return makePopupInfo(
        row,
        "fa-solid fa-calendar-days fa-xl event-detail-row-icon",
      );
    };

    const makePopupLocation = (event: EventImpl) => {
      if (event.extendedProps.location === null) {
        return null;
      }
      const info = document.createElement("div");
      info.innerText = event.extendedProps.location;

      return makePopupInfo(info, "fa-solid fa-location-dot");
    };

    const makePopupUrl = (event: EventImpl) => {
      if (event.url === "") {
        return null;
      }
      const url = document.createElement("a");
      url.href = event.url;
      url.textContent = gettext("More info");

      return makePopupInfo(url, "fa-solid fa-link");
    };

    // Create new popup
    const popup = document.createElement("div");
    const popupContainer = document.createElement("div");

    popup.setAttribute("id", "event-details");
    popupContainer.setAttribute("class", "event-details-container");

    popupContainer.appendChild(makePopupTitle(event.event));

    const location = makePopupLocation(event.event);
    if (location !== null) {
      popupContainer.appendChild(location);
    }

    const url = makePopupUrl(event.event);
    if (url !== null) {
      popupContainer.appendChild(url);
    }

    popup.appendChild(popupContainer);

    // We can't just add the element relative to the one we want to appear under
    // Otherwise, it either gets clipped by the boundaries of the calendar or resize cells
    // Here, we create a popup outside the calendar that follows the clicked element
    this.node.appendChild(popup);
    const follow = (node: HTMLElement) => {
      const rect = node.getBoundingClientRect();
      popup.setAttribute(
        "style",
        `top: calc(${rect.top + window.scrollY}px + ${rect.height}px); left: ${rect.left + window.scrollX}px;`,
      );
    };
    follow(event.el);
    window.addEventListener("resize", () => {
      follow(event.el);
    });
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
      eventClick: (event) => {
        // Avoid our popup to be deleted because we clicked outside of it
        event.jsEvent.stopPropagation();
        // Don't auto-follow events URLs
        event.jsEvent.preventDefault();
        this.createEventDetailPopup(event);
      },
    });
    this.calendar.render();

    window.addEventListener("click", (event: MouseEvent) => {
      // Auto close popups when clicking outside of it
      const popup = document.getElementById("event-details");
      if (popup !== null && !popup.contains(event.target as Node)) {
        popup.remove();
      }
    });
  }
}
