function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function get_starting_items() {
    const cookie = getCookie("basket_items")
    try {
        // django cookie backend does an utter mess on non-trivial data types
        // so we must perform a conversion of our own
        const biscuit = JSON.parse(JSON.parse(cookie.replace(/\\054/g, ',')));
        if (Array.isArray(biscuit)) {
            return biscuit;
        }
        return [];
    } catch (e) {
        return [];
    }
}

document.addEventListener('alpine:init', () => {
    Alpine.data('basket', () => ({
        items: get_starting_items(),

        get_total() {
            let total = 0;
            for (const item of this.items) {
                total += item["quantity"] * item["unit_price"];
            }
            return total;
        },

        add(item) {
            item.quantity++;
            this.edit_cookies()
        },

        remove(item_id) {
            const index = this.items.findIndex(e => e.id === item_id);
            if (index < 0) return;
            this.items[index].quantity -= 1;
            if (this.items[index].quantity === 0) {
                this.items = this.items.filter((e) => e.id !== this.items[index].id);
            }
            this.edit_cookies();
        },

        clear_basket() {
            this.items = []
            this.edit_cookies();
        },

        edit_cookies() {
            // a cookie survives an hour
            console.log(encodeURIComponent(JSON.stringify(this.items)));
            document.cookie = "basket_items=" + encodeURIComponent(JSON.stringify(this.items)) + ";Max-Age=3600";
        },

        /**
         * Create an item in the basket if it was not already in
         * @param id : int the id of the product to add
         * @param name : String the name of the product
         * @param price : number the unit price of the product
         */
        create_item(id, name, price) {
            let new_item = {
                id: id,
                name: name,
                quantity: 0,
                unit_price: price
            };
            this.items.push(new_item);
            this.add(new_item);
        },

        /**
         * add an item to the basket.
         * This is called when the user click
         * on a button in the catalog (left side of the page)
         * @param id : int the id of the product to add
         * @param name : String the name of the product
         * @param price : number the unit price of the product
         */
        add_from_catalog(id, name, price) {
            const item = this.items.find(e => e.id === id)
            if (item === undefined) {
                this.create_item(id, name, price);
            } else {
                // the user clicked on an item which is already in the basket
                this.add(item);
            }
        },
    }))
})