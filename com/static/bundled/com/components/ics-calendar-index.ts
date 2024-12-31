import { makeUrl } from "#core:utils/api";
import { inheritHtmlElement, registerComponent } from "#core:utils/web-components";
import { Calendar, type EventClickArg } from "@fullcalendar/core";
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

    // Create new popup
    const popup = document.createElement("div");
    const popupContainer = document.createElement("div");
    const popupFirstRow = document.createElement("div");
    const popupTitleTimeIcon = document.createElement("i");
    const popupTitleTime = document.createElement("div");
    const popupTitle = document.createElement("h4");
    const popupTime = document.createElement("span");

    popup.setAttribute("id", "event-details");
    popupContainer.setAttribute("class", "event-details-container");
    popupFirstRow.setAttribute("class", "event-details-row");

    popupTitleTimeIcon.setAttribute(
      "class",
      "fa-solid fa-calendar-days fa-xl event-detail-row-icon",
    );

    popupTitle.setAttribute("class", "event-details-row-content");
    popupTitle.textContent = event.event.title;

    popupTime.setAttribute("class", "event-details-row-content");
    popupTime.textContent = `${this.formatDate(event.event.start)} - ${this.formatDate(event.event.end)}`;

    popupTitleTime.appendChild(popupTitle);
    popupTitleTime.appendChild(popupTime);

    popupFirstRow.appendChild(popupTitleTimeIcon);
    popupFirstRow.appendChild(popupTitleTime);

    popupContainer.appendChild(popupFirstRow);

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
