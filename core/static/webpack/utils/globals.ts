import type { Alpine as AlpineType } from "alpinejs";

declare global {
  const Alpine: AlpineType;
  const gettext: (text: string) => string;
}
