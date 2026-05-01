import type { CounterItem } from "#counter:counter/types";

export class BasketItem {
  quantity: number;
  product: CounterItem;
  errors: string[];

  constructor(product: CounterItem, quantity: number) {
    this.quantity = quantity;
    this.product = product;
    this.errors = [];
  }

  getBonusQuantity(): number {
    if (!this.product.hasTrayPrice) {
      return 0;
    }
    return Math.floor(this.quantity / this.product.quantityForTrayPrice);
  }

  sum(): number {
    return (this.quantity - this.getBonusQuantity()) * this.product.price.amount;
  }
}
