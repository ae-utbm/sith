import type { Product } from "#counter:counter/types.ts";

export class BasketItem {
  quantity: number;
  product: Product;
  quantityForTrayPrice: number;
  errors: string[];

  constructor(product: Product, quantity: number) {
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
    return (this.quantity - this.getBonusQuantity()) * this.product.price;
  }
}
