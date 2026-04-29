export type ErrorMessage = string;

export interface InitialFormData {
  /* Used to refill the form when the backend raises an error */
  id?: keyof Record<string, CounterItem>;
  quantity?: number;
  errors?: string[];
}

export interface ProductFormula {
  result: number;
  products: number[];
}

export interface CounterConfig {
  customerBalance: number;
  customerId: number;
  products: Record<string, CounterItem>;
  formulas: ProductFormula[];
  formInitial: InitialFormData[];
  cancelUrl: string;
}

interface Price {
  id: number;
  amount: number;
}

export interface CounterItem {
  productId: number;
  price: Price;
  code: string;
  name: string;
  hasTrayPrice: boolean;
  quantityForTrayPrice: number;
}
