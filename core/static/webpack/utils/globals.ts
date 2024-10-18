import type { Alpine as AlpineType } from "alpinejs";

declare global {
  const Alpine: AlpineType;
  const gettext: (text: string) => string;
  const interpolate: <T>(fmt: string, args: string[] | T, isNamed?: boolean) => string;
}

/**
 * Helper function to export typescript functions to regular html and jinja files
 * Without it, you either have to use the any keyword and suppress warnings or do a
 * very painful type conversion workaround which is only here to please the linter
 *
 * This is only useful if you're using typescript, this is equivalent to doing
 * window.yourFunction = yourFunction
 **/
// biome-ignore lint/suspicious/noExplicitAny: Avoid strange tricks to export functions
export function exportToHtml(name: string, func: any) {
  // biome-ignore lint/suspicious/noExplicitAny: Avoid strange tricks to export functions
  (window as any)[name] = func;
}
