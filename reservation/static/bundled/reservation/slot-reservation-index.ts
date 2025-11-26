import { AlertMessage } from "#core:utils/alert-message";
import type { SlotSelectedEventArg } from "#reservation:reservation/types";

document.addEventListener("alpine:init", () => {
  Alpine.data("slotReservation", () => ({
    start: null as string,
    end: null as string,
    room: null as number,
    showForm: false,

    init() {
      document.addEventListener(
        "timeSlotSelected",
        (event: CustomEvent<SlotSelectedEventArg>) => {
          this.start = event.detail.start.split("+")[0];
          this.end = event.detail.end.split("+")[0];
          this.room = event.detail.ressource;
          this.showForm = true;
          this.$nextTick(() => this.$el.scrollIntoView({ behavior: "smooth" })).then();
        },
      );
    },
  }));

  /**
   * Component that will catch events sent from the scheduler
   * to display success messages accordingly.
   */
  Alpine.data("scheduleMessages", () => ({
    alertMessage: new AlertMessage({ defaultDuration: 2000 }),
    init() {
      document.addEventListener("reservationSlotChanged", (_event: CustomEvent) => {
        this.alertMessage.display(gettext("This slot has been successfully moved"), {
          success: true,
        });
      });
    },
  }));
});
