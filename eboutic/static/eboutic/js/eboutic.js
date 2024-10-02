/* eslint-disable camelcase */
/**
 * @typedef {Object} BasketItem An item in the basket
 * @property {number} id The id of the product
 * @property {string} name The name of the product
 * @property {number} quantity The quantity of the product
 * @property {number} unit_price The unit price of the product
 */

const BASKET_ITEMS_COOKIE_NAME = 'basket_items'

/**
 * Search for a cookie by name
 * @param {string} name Name of the cookie to get
 * @returns {string|null|undefined} the value of the cookie or null if it does not exist, undefined if not found
 */
function getCookie (name) {
  if (!document.cookie || document.cookie.length === 0) return null

  const found = document.cookie
    .split(';')
    .map(c => c.trim())
    .find(c => c.startsWith(name + '='))

  return found === undefined ? undefined : decodeURIComponent(found.split('=')[1])
}

/**
 * Fetch the basket items from the associated cookie
 * @returns {BasketItem[]|[]} the items in the basket
 */
function get_starting_items () {
  const cookie = getCookie(BASKET_ITEMS_COOKIE_NAME)
  if (!cookie) {
    return []
  }
  // Django cookie backend converts `,` to `\054`
  let parsed = JSON.parse(cookie.replace(/\\054/g, ','))
  if (typeof parsed === 'string') {
    // In some conditions, a second parsing is needed
    parsed = JSON.parse(parsed)
  }
  const res = Array.isArray(parsed) ? parsed : []
  return res.filter((i) => !!document.getElementById(i.id))
}

document.addEventListener('alpine:init', () => {
  Alpine.data('basket', () => ({
    items: get_starting_items(),

    /**
         * Get the total price of the basket
         * @returns {number} The total price of the basket
         */
    get_total () {
      return this.items
        .reduce((acc, item) => acc + item.quantity * item.unit_price, 0)
    },

    /**
         * Add 1 to the quantity of an item in the basket
         * @param {BasketItem} item
         */
    add (item) {
      item.quantity++
      this.set_cookies()
    },

    /**
         * Remove 1 to the quantity of an item in the basket
         * @param {BasketItem} item_id
         */
    remove (item_id) {
      const index = this.items.findIndex(e => e.id === item_id)

      if (index < 0) return
      this.items[index].quantity -= 1

      if (this.items[index].quantity === 0) {
        this.items = this.items.filter((e) => e.id !== this.items[index].id)
      }
      this.set_cookies()
    },

    /**
         * Remove all the items from the basket & cleans the catalog CSS classes
         */
    clear_basket () {
      this.items = []
      this.set_cookies()
    },

    /**
         * Set the cookie in the browser with the basket items
         * ! the cookie survives an hour
         */
    set_cookies () {
      if (this.items.length === 0) {
        document.cookie = `${BASKET_ITEMS_COOKIE_NAME}=;Max-Age=0`
      } else {
        document.cookie = `${BASKET_ITEMS_COOKIE_NAME}=${encodeURIComponent(JSON.stringify(this.items))};Max-Age=3600`
      }
    },

    /**
         * Create an item in the basket if it was not already in
         * @param {number} id The id of the product to add
         * @param {string} name The name of the product
         * @param {number} price The unit price of the product
         * @returns {BasketItem} The created item
         */
    create_item (id, name, price) {
      const new_item = {
        id,
        name,
        quantity: 0,
        unit_price: price
      }

      this.items.push(new_item)
      this.add(new_item)

      return new_item
    },

    /**
         * Add an item to the basket.
         * This is called when the user click on a button in the catalog
         * @param {number} id The id of the product to add
         * @param {string} name The name of the product
         * @param {number} price The unit price of the product
         */
    add_from_catalog (id, name, price) {
      let item = this.items.find(e => e.id === id)

      // if the item is not in the basket, we create it
      // else we add + 1 to it
      if (!item) {
        item = this.create_item(id, name, price)
      } else {
        this.add(item)
      }
    }
  }))
})
