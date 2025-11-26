export type ErrorMessage = string;

export interface InitialFormData {
  /* Used to refill the form when the backend raises an error */
  id?: keyof Record<string, Product>;
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
  products: Record<string, Product>;
  formulas: ProductFormula[];
  formInitial: InitialFormData[];
  cancelUrl: string;
}

export interface Product {
  id: string;
  code: string;
  name: string;
  price: number;
  hasTrayPrice: boolean;
  quantityForTrayPrice: number;
}
