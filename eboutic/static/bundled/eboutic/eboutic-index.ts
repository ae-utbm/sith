import { versionedLocalStorage } from "#core:core/localstorage";

interface BasketItem {
  priceId: number;
  name: string;
  quantity: number;
  unitPrice: number;
  isRefill: boolean;
}

const BASKET_CACHE_KEY = "basket";
const BASKET_CACHE_VERSION = 2;

document.addEventListener("alpine:init", () => {
  Alpine.data("basket", (validPrices: number[], lastPurchaseTime?: number) => ({
    basket: [] as BasketItem[],

    init() {
      this.basket = this.loadBasket();
      this.$watch("basket", () => {
        this.saveBasket();
      });
      document
        .getElementById("id_form-TOTAL_FORMS")
        ?.setAttribute(":value", "basket.length");
    },

    loadBasket(): BasketItem[] {
      const cached = versionedLocalStorage.getItem<BasketItem[]>(BASKET_CACHE_KEY, {
        version: BASKET_CACHE_VERSION,
      });
      if (!cached) {
        return [];
      }
      if (
        lastPurchaseTime &&
        localStorage.basketTimestamp &&
        new Date(lastPurchaseTime) >=
          new Date(Number.parseInt(localStorage.basketTimestamp, 10))
      ) {
        // Invalidate basket if a purchase was made
        return [];
      }
      // The basket is cached and not expired, so return it,
      // but without items that are invalid
      // (e.g. because the product is archived, or sold out)
      return cached.filter((item) => validPrices.includes(item.priceId));
    },

    saveBasket() {
      versionedLocalStorage.setItem(BASKET_CACHE_KEY, this.basket, {
        version: BASKET_CACHE_VERSION,
      });
      localStorage.setItem("basketTimestamp", Date.now().toString());
    },

    /**
     * Get the total price of the basket
     * @returns {number} The total price of the basket
     */
    getTotal() {
      return this.basket.reduce(
        (acc: number, item: BasketItem) => acc + item.quantity * item.unitPrice,
        0,
      );
    },

    getTotalRefill() {
      return this.basket
        .filter((item) => item.isRefill)
        .reduce(
          (acc: number, item: BasketItem) => acc + item.quantity * item.unitPrice,
          0,
        );
    },

    /**
     * Add 1 to the quantity of an item in the basket
     * @param {BasketItem} item
     */
    add(item: BasketItem) {
      item.quantity++;
    },

    /**
     * Remove 1 to the quantity of an item in the basket
     * @param itemId the id of the item to remove
     */
    remove(itemId: number) {
      const index = this.basket.findIndex((e: BasketItem) => e.priceId === itemId);

      if (index < 0) {
        return;
      }
      this.basket[index].quantity -= 1;

      if (this.basket[index].quantity === 0) {
        this.basket = this.basket.filter(
          (e: BasketItem) => e.priceId !== this.basket[index].priceId,
        );
      }
    },

    /**
     * Remove all the items from the basket & cleans the catalog CSS classes
     */
    clearBasket() {
      this.basket = [];
    },

    /**
     * Create an item in the basket if it was not already in
     * @param id The id of the product to add
     * @param name The name of the product
     * @param price The unit price of the product
     * @param isRefill true if the product is a refill bond
     * @returns The created item
     */
    createItem(id: number, name: string, price: number, isRefill: boolean): BasketItem {
      const newItem = {
        priceId: id,
        name,
        quantity: 0,
        unitPrice: price,
        isRefill,
      } as BasketItem;

      this.basket.push(newItem);
      this.add(newItem);

      return newItem;
    },

    /**
     * Add an item to the basket.
     * This is called when the user click on a button in the catalog
     * @param id The id of the product to add
     * @param name The name of the product
     * @param price The unit price of the product
     * @param isRefill true if the product is a refill bond
     */
    addFromCatalog(id: number, name: string, price: number, isRefill: boolean) {
      const item = this.basket.find((e: BasketItem) => e.priceId === id);

      // if the item is not in the basket, we create it
      // else we add + 1 to it
      if (item) {
        this.add(item);
      } else {
        this.createItem(id, name, price, isRefill);
      }
    },
  }));
});
