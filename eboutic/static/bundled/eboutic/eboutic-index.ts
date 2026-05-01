export {};

interface BasketItem {
  priceId: number;
  name: string;
  quantity: number;
  unitPrice: number;
}

// increment the key number if the data schema of the cached basket changes
const BASKET_CACHE_KEY = "basket1";

document.addEventListener("alpine:init", () => {
  Alpine.data("basket", (lastPurchaseTime?: number) => ({
    basket: [] as BasketItem[],

    init() {
      this.basket = this.loadBasket();
      this.$watch("basket", () => {
        this.saveBasket();
      });
      // Invalidate basket if a purchase was made
      if (lastPurchaseTime !== null && localStorage.basketTimestamp !== undefined) {
        if (
          new Date(lastPurchaseTime) >=
          new Date(Number.parseInt(localStorage.basketTimestamp, 10))
        ) {
          this.basket = [];
        }
      }

      // It's quite tricky to manually apply attributes to the management part
      // of a formset so we dynamically apply it here
      this.$refs.basketManagementForm
        .getElementById("#id_form-TOTAL_FORMS")
        .setAttribute(":value", "basket.length");
    },

    loadBasket(): BasketItem[] {
      if (localStorage.getItem(BASKET_CACHE_KEY) === null) {
        return [];
      }
      try {
        return JSON.parse(localStorage.getItem(BASKET_CACHE_KEY));
      } catch (_err) {
        return [];
      }
    },

    saveBasket() {
      localStorage.setItem(BASKET_CACHE_KEY, JSON.stringify(this.basket));
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
          (e: BasketItem) => e.priceId !== this.basket[index].id,
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
     * @returns The created item
     */
    createItem(id: number, name: string, price: number): BasketItem {
      const newItem = {
        priceId: id,
        name,
        quantity: 0,
        unitPrice: price,
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
     */
    addFromCatalog(id: number, name: string, price: number) {
      let item = this.basket.find((e: BasketItem) => e.priceId === id);

      // if the item is not in the basket, we create it
      // else we add + 1 to it
      if (item) {
        this.add(item);
      } else {
        item = this.createItem(id, name, price);
      }
    },
  }));
});
