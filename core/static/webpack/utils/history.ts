export enum History {
  None = 0,
  Push = 1,
  Replace = 2,
}

export const initialUrlParams = new URLSearchParams(window.location.search);
export const getCurrentUrlParams = () => {
  return new URLSearchParams(window.location.search);
};

export function updateQueryString(
  key: string,
  value?: string | string[],
  action?: History,
  url?: string,
) {
  const historyAction = action ?? History.Replace;
  const ret = new URL(url ?? window.location.href);

  if (value === undefined || value === null || value === "") {
    // If the value is null, undefined or empty => delete it
    ret.searchParams.delete(key);
  } else if (Array.isArray(value)) {
    ret.searchParams.delete(key);
    for (const v of value) {
      ret.searchParams.append(key, v);
    }
  } else {
    ret.searchParams.set(key, value);
  }

  if (historyAction === History.Push) {
    window.history.pushState(null, "", ret.toString());
  } else if (historyAction === History.Replace) {
    window.history.replaceState(null, "", ret.toString());
  }

  return ret;
}
