import { type Notification, NotificationLevel } from "#core:utils/notifications";
import { etransactioninfoFetchEtransactionData } from "#openapi";

interface Basket {
  id: number;
  timeout: Date;
}
document.addEventListener("alpine:init", () => {
  Alpine.data("etransaction", (initialData, basket: Basket) => ({
    data: initialData,
    isCbAvailable: Object.keys(initialData).length > 0,
    isSithAvailable: true,

    init() {
      const now = new Date();
      const timeout = basket.timeout.getTime() - now.getTime();
      if (timeout <= 0) {
        // basket was already outdated at initial page load
        this.timeoutBasket();
      } else {
        setTimeout(() => this.timeoutBasket(), timeout);
      }
    },

    /**
     * Make this basket into a timeout state.
     * All submission inputs are disabled, and an error message is displayed.
     */
    timeoutBasket() {
      this.isCbAvailable = false;
      this.isSithAvailable = false;
      const message = gettext("Basket expired");

      const existingNotif: Notification | undefined = this.$notifications
        .getAll()
        .find(
          (n: Notification) =>
            n.tag === NotificationLevel.Error && n.message === message,
        );
      if (existingNotif === undefined) {
        this.$notifications.error(message);
      }
    },

    /**
     * Refresh the data used for etransaction.
     *
     * Note: if this is called while the basket is expired, it will be a no-op
     */
    async fill() {
      if (new Date() > basket.timeout) {
        // refresh etransaction data only if the basket is still valid.
        this.timeoutBasket();
        return;
      }
      this.isCbAvailable = false;
      const res = await etransactioninfoFetchEtransactionData({
        // biome-ignore lint/style/useNamingConvention: api is in snake_case
        path: { basket_id: basket.id },
      });
      if (res.response.ok) {
        this.data = res.data;
        this.isCbAvailable = true;
      } else if (res.response.status === 410) {
        // The basket is expired, so no payment method should be available at all.
        // This shouldn't happen, because we don't send the request
        // when the timeout is passed, but we are better safe than sorry
        this.timeoutBasket();
      }
    },
  }));
});
