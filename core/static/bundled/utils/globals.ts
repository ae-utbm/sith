import type { Alpine as AlpineType } from "alpinejs";

declare global {
  const Alpine: AlpineType;
  const gettext: (text: string) => string;
  const interpolate: <T>(fmt: string, args: string[] | T, isNamed?: boolean) => string;
}
