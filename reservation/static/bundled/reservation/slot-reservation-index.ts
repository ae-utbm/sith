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
});
