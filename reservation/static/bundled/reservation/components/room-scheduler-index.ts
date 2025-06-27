import { inheritHtmlElement, registerComponent } from "#core:utils/web-components";
import {
  Calendar,
  type EventDropArg,
  type EventSourceFuncArg,
} from "@fullcalendar/core";
import enLocale from "@fullcalendar/core/locales/en-gb";
import frLocale from "@fullcalendar/core/locales/fr";

import {
  type ReservationslotFetchSlotsData,
  type SlotSchema,
  reservableroomFetchRooms,
  reservationslotFetchSlots,
  reservationslotUpdateSlot,
} from "#openapi";

import { paginated } from "#core:utils/api";
import interactionPlugin from "@fullcalendar/interaction";
import resourceTimelinePlugin from "@fullcalendar/resource-timeline";

@registerComponent("room-scheduler")
export class RoomScheduler extends inheritHtmlElement("div") {
  static observedAttributes = ["locale", "can_edit_slot", "can_create_slot"];
  private scheduler: Calendar;
  private locale = "en";
  private canEditSlot = false;
  private canBookSlot = false;

  attributeChangedCallback(name: string, _oldValue?: string, newValue?: string) {
    if (name === "locale") {
      this.locale = newValue;
    }
    if (name === "can_edit_slot") {
      this.canEditSlot = newValue.toLowerCase() === "true";
    }
    if (name === "can_create_slot") {
      this.canBookSlot = newValue.toLowerCase() === "true";
    }
  }

  /**
   * Fetch the events displayed in the timeline.
   * cf https://fullcalendar.io/docs/events-function
   */
  async fetchEvents(fetchInfo: EventSourceFuncArg) {
    const res: SlotSchema[] = await paginated(reservationslotFetchSlots, {
      query: { after: fetchInfo.startStr, before: fetchInfo.endStr },
    } as ReservationslotFetchSlotsData);
    return res.map((i) =>
      Object.assign(i, {
        title: `${i.author.first_name} ${i.author.last_name}`,
        resourceId: i.room,
        editable: new Date(i.start) > new Date(),
      }),
    );
  }

  /**
   * Fetch the resources which events are associated with.
   * cf https://fullcalendar.io/docs/resources-function
   */
  async fetchResources() {
    const res = await reservableroomFetchRooms();
    return res.data.map((i) => Object.assign(i, { title: i.name, group: i.location }));
  }

  /**
   * Send a request to the API to change
   * the start and the duration of a reservation slot
   */
  async changeReservation(args: EventDropArg) {
    const duration = new Date(args.event.end.getTime() - args.event.start.getTime());
    const response = await reservationslotUpdateSlot({
      // biome-ignore lint/style/useNamingConvention: api is snake_case
      path: { slot_id: Number.parseInt(args.event.id) },
      query: {
        start: args.event.startStr,
        duration: `PT${duration.getUTCHours()}H${duration.getUTCMinutes()}M${duration.getUTCSeconds()}S`,
      },
    });
    if (response.response.ok) {
      this.scheduler.refetchEvents();
    }
  }

  connectedCallback() {
    super.connectedCallback();
    this.scheduler = new Calendar(this.node, {
      schedulerLicenseKey: "GPL-My-Project-Is-Open-Source",
      initialView: "resourceTimelineDay",
      headerToolbar: {
        left: "prev,next today",
        center: "title",
        right: "resourceTimelineDay,resourceTimelineWeek",
      },
      plugins: [resourceTimelinePlugin, interactionPlugin],
      locales: [frLocale, enLocale],
      height: "auto",
      locale: this.locale,
      resourceGroupField: "group",
      resourceAreaHeaderContent: gettext("Rooms"),
      editable: this.canEditSlot,
      snapDuration: "00:15",
      eventConstraint: { start: new Date() }, // forbid edition of past events
      eventOverlap: false,
      eventResourceEditable: false,
      refetchResourcesOnNavigate: true,
      resourceAreaWidth: "20%",
      resources: this.fetchResources,
      events: this.fetchEvents,
      selectOverlap: false,
      selectable: this.canBookSlot,
      selectConstraint: { start: new Date() },
      nowIndicator: true,
      eventDrop: this.changeReservation,
    });
    this.scheduler.render();
  }
}
