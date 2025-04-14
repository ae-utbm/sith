export {};

interface BasketItem {
  id: number;
  name: string;
  quantity: number;
  // biome-ignore lint/style/useNamingConvention: the python code is snake_case
  unit_price: number;
}

document.addEventListener("alpine:init", () => {
  Alpine.data("basket", () => ({
    basket: [] as BasketItem[],

    init() {
      this.basket = this.loadBasket();
      this.$watch("basket", () => {
        this.saveBasket();
      });

      // It's quite tricky to manually apply attributes to the management part
      // of a formset so we dynamically apply it here
      this.$refs.basketManagementForm
        .querySelector("#id_form-TOTAL_FORMS")
        .setAttribute(":value", "basket.length");
    },

    loadBasket(): BasketItem[] {
      if (localStorage.basket === undefined) {
        return [];
      }
      try {
        return JSON.parse(localStorage.basket);
      } catch (_err) {
        return [];
      }
    },

    saveBasket() {
      localStorage.basket = JSON.stringify(this.basket);
    },

    /**
     * Get the total price of the basket
     * @returns {number} The total price of the basket
     */
    getTotal() {
      return this.basket.reduce(
        (acc: number, item: BasketItem) => acc + item.quantity * item.unit_price,
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
      const index = this.basket.findIndex((e: BasketItem) => e.id === itemId);

      if (index < 0) {
        return;
      }
      this.basket[index].quantity -= 1;

      if (this.basket[index].quantity === 0) {
        this.basket = this.basket.filter(
          (e: BasketItem) => e.id !== this.basket[index].id,
        );
      }
    },

    /**
     * Remove all the basket from the basket & cleans the catalog CSS classes
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
        id,
        name,
        quantity: 0,
        // biome-ignore lint/style/useNamingConvention: the python code is snake_case
        unit_price: price,
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
      let item = this.basket.find((e: BasketItem) => e.id === id);

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
