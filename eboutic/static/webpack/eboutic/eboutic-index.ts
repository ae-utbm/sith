export {};

interface BasketItem {
  id: number;
  name: string;
  quantity: number;
  // biome-ignore lint/style/useNamingConvention: the python code is snake_case
  unit_price: number;
}

const BASKET_ITEMS_COOKIE_NAME: string = "basket_items";

/**
 * Search for a cookie by name
 * @param name Name of the cookie to get
 * @returns the value of the cookie or null if it does not exist, undefined if not found
 */
function getCookie(name: string): string | null | undefined {
  if (!document.cookie || document.cookie.length === 0) {
    return null;
  }

  const found = document.cookie
    .split(";")
    .map((c) => c.trim())
    .find((c) => c.startsWith(`${name}=`));

  return found === undefined ? undefined : decodeURIComponent(found.split("=")[1]);
}

/**
 * Fetch the basket items from the associated cookie
 * @returns the items in the basket
 */
function getStartingItems(): BasketItem[] {
  const cookie = getCookie(BASKET_ITEMS_COOKIE_NAME);
  if (!cookie) {
    return [];
  }
  // Django cookie backend converts `,` to `\054`
  let parsed = JSON.parse(cookie.replace(/\\054/g, ","));
  if (typeof parsed === "string") {
    // In some conditions, a second parsing is needed
    parsed = JSON.parse(parsed);
  }
  const res = Array.isArray(parsed) ? parsed : [];
  return res.filter((i) => !!document.getElementById(i.id));
}

document.addEventListener("alpine:init", () => {
  Alpine.data("basket", () => ({
    items: getStartingItems() as BasketItem[],

    /**
     * Get the total price of the basket
     * @returns {number} The total price of the basket
     */
    getTotal() {
      return this.items.reduce(
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
      this.setCookies();
    },

    /**
     * Remove 1 to the quantity of an item in the basket
     * @param itemId the id of the item to remove
     */
    remove(itemId: number) {
      const index = this.items.findIndex((e: BasketItem) => e.id === itemId);

      if (index < 0) {
        return;
      }
      this.items[index].quantity -= 1;

      if (this.items[index].quantity === 0) {
        this.items = this.items.filter(
          (e: BasketItem) => e.id !== this.items[index].id,
        );
      }
      this.setCookies();
    },

    /**
     * Remove all the items from the basket & cleans the catalog CSS classes
     */
    clearBasket() {
      this.items = [];
      this.setCookies();
    },

    /**
     * Set the cookie in the browser with the basket items
     * ! the cookie survives an hour
     */
    setCookies() {
      if (this.items.length === 0) {
        document.cookie = `${BASKET_ITEMS_COOKIE_NAME}=;Max-Age=0`;
      } else {
        document.cookie = `${BASKET_ITEMS_COOKIE_NAME}=${encodeURIComponent(JSON.stringify(this.items))};Max-Age=3600`;
      }
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

      this.items.push(newItem);
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
      let item = this.items.find((e: BasketItem) => e.id === id);

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
