// increment this number when a breaking change is made with localStorage
const CURRENT_CACHE_VERSION = 1;

export function cacheBuster() {
  const version = Number.parseInt(localStorage.getItem("version") ?? "0", 10);
  if (version === CURRENT_CACHE_VERSION) {
    // The cache schema is up-to-date. Nothing to do.
    return;
  }
  localStorage.removeItem("basket");
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
  localStorage.setItem("version", CURRENT_CACHE_VERSION.toString());
}
