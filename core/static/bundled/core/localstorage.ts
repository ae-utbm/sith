/**
 * For more detailed infos on how to use this file,
 * check /docs/tutorial/front/localstorage.md,
 * or https://ae-utbm.github.io/sith/tutorial/front/localstorage/
 */

// increment this number when a breaking change is made with localStorage
const CURRENT_LOCALSTORAGE_VERSION = 1;

/**
 * Remove keys that are no longer used from localStorage
 */
export function expireOldStorage() {
  const version = Number.parseInt(localStorage.getItem("version") ?? "0", 10);
  if (version === CURRENT_LOCALSTORAGE_VERSION) {
    // The cache schema is up-to-date. Nothing to do.
    return;
  }
  localStorage.removeItem("basket1");
  // remove all storage items which key is in the form
  // `userXXXPictures` or `userXXXPicturesNumber`
  Object.keys(localStorage)
    .filter(
      (key) =>
        key.startsWith("user") &&
        (key.endsWith("Pictures") || key.endsWith("PicturesNumber")),
    )
    .forEach((key) => {
      localStorage.removeItem(key);
    });
  localStorage.setItem("version", CURRENT_LOCALSTORAGE_VERSION.toString());
}

interface VersionedStorageItem<T> {
  version?: number;
  val: T | undefined;
}

export const versionedLocalStorage = {
  ...localStorage,
  /**
   * set this item in localStorage, alongside its version.
   *
   * Note: this expects an object, not a JSON string, because the parsing
   * into JSON needs to be done inside the function.
   */
  setItem<T>(key: string, value: T, { version }: { version: number }) {
    localStorage.setItem(key, JSON.stringify({ version: version, val: value }));
  },
  /**
   * Get the item linked with the given key and version from localStorage.
   *
   * Note: if the given key exists in localStorage but doesn't satisfy
   * the given version, it will be cleared from cache.
   *
   * @return the object if found and with the good version, else null;
   */
  getItem<T>(key: string, { version }: { version: number }): T | null {
    const stored = localStorage.getItem(key);
    if (!stored) {
      // this key doesn't exist, return null;
      return null;
    }
    const obj: VersionedStorageItem<T> = JSON.parse(stored);
    if (obj.version !== version || obj.val === undefined) {
      // The version is wrong, return null and remove this item from cache
      localStorage.removeItem(key);
      return null;
    }
    return obj.val;
  },
};
