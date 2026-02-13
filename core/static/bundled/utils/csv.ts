import type { NestedKeyOf } from "#core:utils/types.ts";

interface StringifyOptions<T extends object> {
  /** The columns to include in the resulting CSV. */
  columns: readonly NestedKeyOf<T>[];
  /** Content of the first row */
  titleRow?: readonly string[];
}

function getNested<T extends object>(obj: T, key: NestedKeyOf<T>) {
  const path: (keyof object)[] = key.split(".") as (keyof unknown)[];
  let res = obj[path.shift() as keyof T];
  for (const node of path) {
    if (res === null) {
      break;
    }
    res = res[node];
  }
  return res;
}

/**
 * Convert the content the string to make sure it won't break
 * the resulting csv.
 * cf. https://en.wikipedia.org/wiki/Comma-separated_values#Basic_rules
 */
function sanitizeCell(content: string): string {
  return `"${content.replace(/"/g, '""')}"`;
}

export const csv = {
  stringify: <T extends object>(objs: T[], options?: StringifyOptions<T>) => {
    const columns = options.columns;
    const content = objs
      .map((obj) => {
        return columns
          .map((col) => {
            return sanitizeCell((getNested(obj, col) ?? "").toString());
          })
          .join(",");
      })
      .join("\n");
    if (!options.titleRow) {
      return content;
    }
    const firstRow = options.titleRow.map(sanitizeCell).join(",");
    return `${firstRow}\n${content}`;
  },
};
