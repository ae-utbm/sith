import { Calendar, type EventClickArg, type EventContentArg } from "@fullcalendar/core";
import type { EventImpl } from "@fullcalendar/core/internal";
import enLocale from "@fullcalendar/core/locales/en-gb";
import frLocale from "@fullcalendar/core/locales/fr";
import dayGridPlugin from "@fullcalendar/daygrid";
import iCalendarPlugin from "@fullcalendar/icalendar";
import listPlugin from "@fullcalendar/list";
import { type HTMLTemplateResult, html, render } from "lit-html";
import { makeUrl } from "#core:utils/api.ts";
import { inheritHtmlElement, registerComponent } from "#core:utils/web-components.ts";
import {
  calendarCalendarInternal,
  calendarCalendarUnpublished,
  newsDeleteNews,
  newsPublishNews,
  newsUnpublishNews,
} from "#openapi";

@registerComponent("ics-calendar")
export class IcsCalendar extends inheritHtmlElement("div") {
  static observedAttributes = ["locale", "can_moderate", "can_delete", "ics-help-url"];
  private calendar: Calendar;
  private locale = "en";
  private canModerate = false;
  private canDelete = false;
  private helpUrl = "";

  // Hack variable to detect recurring events
  // The underlying ics library doesn't include any info about rrules
  // That's why we have to detect those events ourselves
  private recurrenceMap: Map<string, EventImpl> = new Map();

  attributeChangedCallback(name: string, _oldValue?: string, newValue?: string) {
    if (name === "locale") {
      this.locale = newValue;
    }
    if (name === "can_moderate") {
      this.canModerate = newValue.toLowerCase() === "true";
    }
    if (name === "can_delete") {
      this.canDelete = newValue.toLowerCase() === "true";
    }

    if (name === "ics-help-url") {
      this.helpUrl = newValue;
    }
  }

  isMobile() {
    return window.innerWidth < 765;
  }

  currentView() {
    // Get view type based on viewport
    return this.isMobile() ? "listMonth" : "dayGridMonth";
  }

  currentFooterToolbar() {
    if (this.isMobile()) {
      return {
        start: "",
        center: "getCalendarLink helpButton",
        end: "",
      };
    }
    return { start: "getCalendarLink helpButton", center: "", end: "" };
  }

  currentHeaderToolbar() {
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

  getNewsId(event: EventImpl) {
    return Number.parseInt(
      event.url
        .toString()
        .split("/")
        .filter((s) => s) // Remove blank characters
        .pop(),
      10,
    );
  }

  refreshEvents() {
    this.click(); // Remove focus from popup
    this.recurrenceMap.clear(); // Avoid double detection of the same non recurring event
    this.calendar.refetchEvents();
  }

  async publishNews(id: number) {
    await newsPublishNews({
      path: {
        // biome-ignore lint/style/useNamingConvention: python API
        news_id: id,
      },
    });
    this.dispatchEvent(
      new CustomEvent("calendar-publish", {
        bubbles: true,
        detail: {
          id: id,
        },
      }),
    );
    this.refreshEvents();
  }

  async unpublishNews(id: number) {
    await newsUnpublishNews({
      path: {
        // biome-ignore lint/style/useNamingConvention: python API
        news_id: id,
      },
    });
    this.dispatchEvent(
      new CustomEvent("calendar-unpublish", {
        bubbles: true,
        detail: {
          id: id,
        },
      }),
    );
    this.refreshEvents();
  }

  async deleteNews(id: number) {
    await newsDeleteNews({
      path: {
        // biome-ignore lint/style/useNamingConvention: python API
        news_id: id,
      },
    });
    this.dispatchEvent(
      new CustomEvent("calendar-delete", {
        bubbles: true,
        detail: {
          id: id,
        },
      }),
    );
    this.refreshEvents();
  }

  async getEventSources() {
    const tagRecurringEvents = (eventData: EventImpl) => {
      // This functions tags events with a similar event url
      // We rely on the fact that the event url is always the same
      // for recurring events and always different for single events
      const firstEvent = this.recurrenceMap.get(eventData.url);
      if (firstEvent !== undefined) {
        eventData.extendedProps.isRecurring = true;
        firstEvent.extendedProps.isRecurring = true; // Don't forget the first event
      }
      this.recurrenceMap.set(eventData.url, eventData);
    };
    return [
      {
        url: `${await makeUrl(calendarCalendarInternal)}`,
        format: "ics",
        className: "internal",
        cache: false,
        eventDataTransform: tagRecurringEvents,
      },
      {
        url: `${await makeUrl(calendarCalendarUnpublished)}`,
        format: "ics",
        color: "red",
        className: "unpublished",
        cache: false,
        eventDataTransform: tagRecurringEvents,
      },
    ];
  }

  createEventDetailPopup(event: EventClickArg) {
    // Delete previous popup
    const oldPopup = document.getElementById("event-details");
    if (oldPopup !== null) {
      oldPopup.remove();
    }

    const makePopupInfo = (info: HTMLTemplateResult, iconClass: string) => {
      return html`
        <div class="event-details-row">
          <i class="event-detail-row-icon fa-xl ${iconClass}"></i>
          ${info}
        </div>
      `;
    };

    const makePopupTitle = (event: EventImpl) => {
      const row = html`
        <div>
          <h4 class="event-details-row-content">
            ${event.title}
          </h4>
          <span class="event-details-row-content">
            ${this.formatDate(event.start)} - ${this.formatDate(event.end)}
          </span>
        </div>
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
      const info = html`
        <div>
          ${event.extendedProps.location}
        </div>
      `;
      return makePopupInfo(info, "fa-solid fa-location-dot");
    };

    const makePopupUrl = (event: EventImpl) => {
      if (event.url === "") {
        return null;
      }
      const url = html`<a href="${event.url}">${gettext("More info")}</a>`;
      return makePopupInfo(url, "fa-solid fa-link");
    };

    const makePopupTools = (event: EventImpl) => {
      if (!(this.canDelete || this.canModerate)) {
        return null;
      }
      const newsId = this.getNewsId(event);
      const buttons = [] as HTMLTemplateResult[];

      if (this.canModerate) {
        if (event.source.internalEventSource.ui.classNames.includes("unpublished")) {
          const button = html`
            <button class="btn btn-green" @click="${() => this.publishNews(newsId)}">
              <i class="fa fa-check"></i>${gettext("Publish")}
            </button>
          `;
          buttons.push(button);
        } else {
          const button = html`
            <button class="btn btn-orange" @click="${() => this.unpublishNews(newsId)}">
              <i class="fa fa-times"></i>${gettext("Unpublish")}
            </button>
          `;
          buttons.push(button);
        }
      }
      if (this.canDelete) {
        const button = html`
          <button class="btn btn-red" @click="${() => this.deleteNews(newsId)}">
            <i class="fa fa-trash-can"></i>${gettext("Delete")}
          </button>
        `;
        buttons.push(button);
      }

      return makePopupInfo(html`<div>${buttons}</div>`, "fa-solid fa-toolbox");
    };

    // Create new popup
    const infos = [] as HTMLTemplateResult[];
    infos.push(makePopupTitle(event.event));

    const location = makePopupLocation(event.event);
    if (location !== null) {
      infos.push(location);
    }

    const url = makePopupUrl(event.event);
    if (url !== null) {
      infos.push(url);
    }

    const tools = makePopupTools(event.event);
    if (tools !== null) {
      infos.push(tools);
    }

    const popup = document.createElement("div");
    popup.setAttribute("id", "event-details");
    render(html`<div class="event-details-container">${infos}</div>`, popup);

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
      customButtons: {
        getCalendarLink: {
          text: gettext("Copy calendar link"),
          click: async (event: Event) => {
            const button = event.target as HTMLButtonElement;
            button.classList.add("text-copy");
            button.setAttribute("tooltip-class", "calendar-copy-tooltip");
            if (!button.hasAttribute("tooltip-position")) {
              button.setAttribute("tooltip-position", "top");
            }
            if (button.classList.contains("text-copied")) {
              button.classList.remove("text-copied");
            }
            button.setAttribute("tooltip", gettext("Link copied"));
            navigator.clipboard.writeText(
              new URL(
                await makeUrl(calendarCalendarInternal),
                window.location.origin,
              ).toString(),
            );
            setTimeout(() => {
              button.setAttribute("tooltip-class", "calendar-copy-tooltip text-copied");
              button.classList.remove("text-copied");
              button.classList.add("text-copied");
              button.classList.remove("text-copy");
            }, 1500);
          },
        },
        helpButton: {
          text: "?",
          hint: gettext("How to use calendar link"),
          click: () => {
            if (this.helpUrl) {
              window.open(this.helpUrl, "_blank");
            }
          },
        },
      },
      height: "auto",
      locale: this.locale,
      initialView: this.currentView(),
      headerToolbar: this.currentHeaderToolbar(),
      footerToolbar: this.currentFooterToolbar(),
      eventSources: await this.getEventSources(),
      lazyFetching: false,
      windowResize: () => {
        this.calendar.changeView(this.currentView());
        this.calendar.setOption("headerToolbar", this.currentHeaderToolbar());
        this.calendar.setOption("footerToolbar", this.currentFooterToolbar());
      },
      eventClick: (event) => {
        // Avoid our popup to be deleted because we clicked outside of it
        event.jsEvent.stopPropagation();
        // Don't auto-follow events URLs
        event.jsEvent.preventDefault();
        this.createEventDetailPopup(event);
      },
      eventClassNames: (classNamesEvent: EventContentArg) => {
        const classes: string[] = [];
        if (classNamesEvent.event.extendedProps?.isRecurring) {
          classes.push("recurring");
        }

        return classes;
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
