import { makeUrl } from "#core:utils/api";
import { inheritHtmlElement, registerComponent } from "#core:utils/web-components";
import { Calendar, type EventClickArg } from "@fullcalendar/core";
import type { EventImpl } from "@fullcalendar/core/internal";
import enLocale from "@fullcalendar/core/locales/en-gb";
import frLocale from "@fullcalendar/core/locales/fr";
import dayGridPlugin from "@fullcalendar/daygrid";
import iCalendarPlugin from "@fullcalendar/icalendar";
import listPlugin from "@fullcalendar/list";
import {
  calendarCalendarInternal,
  calendarCalendarUnpublished,
  newsDeleteNews,
  newsPublishNews,
  newsUnpublishNews,
} from "#openapi";

@registerComponent("ics-calendar")
export class IcsCalendar extends inheritHtmlElement("div") {
  static observedAttributes = ["locale", "can_moderate", "can_delete"];
  private calendar: Calendar;
  private locale = "en";
  private canModerate = false;
  private canDelete = false;

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
        center: "getCalendarLink",
        end: "",
      };
    }
    return { start: "getCalendarLink", center: "", end: "" };
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
    );
  }

  refreshEvents() {
    this.click(); // Remove focus from popup
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
    return [
      {
        url: `${await makeUrl(calendarCalendarInternal)}`,
        format: "ics",
        className: "internal",
        cache: false,
      },
      {
        url: `${await makeUrl(calendarCalendarUnpublished)}`,
        format: "ics",
        color: "red",
        className: "unpublished",
        cache: false,
      },
    ];
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

    const makePopupTools = (event: EventImpl) => {
      if (!(this.canDelete || this.canModerate)) {
        return null;
      }
      const newsId = this.getNewsId(event);
      const div = document.createElement("div");
      if (this.canModerate) {
        if (event.source.internalEventSource.ui.classNames.includes("unpublished")) {
          const button = document.createElement("button");
          button.innerHTML = `<i class="fa fa-check"></i>${gettext("Publish")}`;
          button.setAttribute("class", "btn btn-green");
          button.onclick = () => {
            this.publishNews(newsId);
          };
          div.appendChild(button);
        } else {
          const button = document.createElement("button");
          button.innerHTML = `<i class="fa fa-times"></i>${gettext("Unpublish")}`;
          button.setAttribute("class", "btn btn-orange");
          button.onclick = () => {
            this.unpublishNews(newsId);
          };
          div.appendChild(button);
        }
      }
      if (this.canDelete) {
        const button = document.createElement("button");
        button.innerHTML = `<i class="fa fa-trash-can"></i>${gettext("Delete")}`;
        button.setAttribute("class", "btn btn-red");
        button.onclick = () => {
          this.deleteNews(newsId);
        };
        div.appendChild(button);
      }

      return makePopupInfo(div, "fa-solid fa-toolbox");
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

    const tools = makePopupTools(event.event);
    if (tools !== null) {
      popupContainer.appendChild(tools);
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
      customButtons: {
        getCalendarLink: {
          text: gettext("Copy calendar link"),
          click: async (event: Event) => {
            const button = event.target as HTMLButtonElement;
            button.classList.add("text-copy");
            if (!button.hasAttribute("position")) {
              button.setAttribute("tooltip", gettext("Link copied"));
              button.setAttribute("position", "top");
              button.setAttribute("no-hover", "");
            }
            if (button.classList.contains("text-copied")) {
              button.classList.remove("text-copied");
            }
            navigator.clipboard.writeText(
              new URL(
                await makeUrl(calendarCalendarInternal),
                window.location.origin,
              ).toString(),
            );
            setTimeout(() => {
              button.classList.remove("text-copied");
              button.classList.add("text-copied");
              button.classList.remove("text-copy");
            }, 1500);
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
