/**
 * Builders to use Select2 in our templates.
 *
 * This comes with two flavours : local data or remote data.
 *
 * # Local data source
 *
 * To use local data source, you must define an array
 * in your JS code, having the fields `id` and `text`.
 *
 * ```js
 * const data = [
 *   {id: 1, text: "foo"},
 *   {id: 2, text: "bar"},
 * ];
 * document.addEventListener("DOMContentLoaded", () => sithSelect2({
 *   element: document.getElementById("select2-input"),
 *   dataSource: localDataSource(data)
 * }));
 * ```
 *
 * You can also define a callback that return ids to exclude :
 *
 * ```js
 * const data = [
 *   {id: 1, text: "foo"},
 *   {id: 2, text: "bar"},
 *   {id: 3, text: "to exclude"},
 * ];
 * document.addEventListener("DOMContentLoaded", () => sithSelect2({
 *   element: document.getElementById("select2-input"),
 *   dataSource: localDataSource(data, {
 *     excluded: () => data.filter((i) => i.text === "to exclude").map((i) => parseInt(i))
 *   })
 * }));
 * ```
 *
 * # Remote data source
 *
 * Select2 with remote data sources are similar to those with local
 * data, but with some more parameters, like `resultConverter`,
 * which takes a callback that must return a `Select2Object`.
 *
 * ```js
 * import { makeUrl } from "#core:utils/api";
 * import {userSearchUsers } from "#openapi"
 * document.addEventListener("DOMContentLoaded", () => sithSelect2({
 *   element: document.getElementById("select2-input"),
 *   dataSource: remoteDataSource(await makeUrl(userSearchUsers), {
 *     excluded: () => [1, 2],  // exclude users 1 and 2 from the search
 *     resultConverter: (user: AjaxResponse) => {id: user.id, text: (user.firstName as UserType)}
 *   })
 * }));
 * ```
 *
 * # Overrides
 *
 * Dealing with a select2 may be complex.
 * That's why, when defining a select,
 * you may add an override parameter,
 * in which you can declare any parameter defined in the
 * Select2 documentation.
 *
 * ```js
 * import { makeUrl } from "#core:utils/api";
 * import {userSearchUsers } from "#openapi"
 * document.addEventListener("DOMContentLoaded", () => sithSelect2({
 *   element: document.getElementById("select2-input"),
 *   dataSource: remoteDataSource(await makeUrl(userSearchUsers), {
 *     resultConverter: (user: AjaxResponse) => {id: user.id, text: (user.firstName as UserType)}
 *     overrides: {
 *      delay: 500
 *     }
 *   })
 * }));
 * ```
 *
 * # Caveats with exclude
 *
 * With local data source, select2 evaluates the data only once.
 * Thus, modify the exclude after the initialisation is a no-op.
 *
 * With remote data source, the exclude list will be evaluated
 * after each api response.
 * It makes it possible to bind the data returned by the callback
 * to some reactive data, thus making the exclude list dynamic.
 *
 * # Images
 *
 * Sometimes, you would like to display an image besides
 * the text on the select items.
 * In this case, fill the `pictureGetter` option :
 *
 * ```js
 * import { makeUrl } from "#core:utils/api";
 * import {userSearchUsers } from "#openapi"
 * document.addEventListener("DOMContentLoaded", () => sithSelect2({
 *   element: document.getElementById("select2-input"),
 *   dataSource: remoteDataSource(await makeUrl(userSearchUsers), {
 *     resultConverter: (user: AjaxResponse) => {id: user.id, text: (user.firstName as UserType)}
 *   })
 *   pictureGetter: (user) => user.profilePict,
 * }));
 * ```
 *
 * # Binding with alpine
 *
 * You can declare your select2 component in an Alpine data.
 *
 * ```html
 * <body>
 *   <div x-data="select2_test">
 *     <select x-ref="search" x-ref="select"></select>
 *     <p x-text="currentSelection.id"></p>
 *     <p x-text="currentSelection.text"></p>
 *   </div>
 * </body>
 *
 * <script>
 * document.addEventListener("alpine:init", () => {
 *   Alpine.data("select2_test", () => ({
 *     selector: undefined,
 *     currentSelect: {id: "", text: ""},
 *
 *     init() {
 *       this.selector = sithSelect2({
 *         element: $(this.$refs.select),
 *         dataSource: localDataSource(
 *           [{id: 1, text: "foo"}, {id: 2, text: "bar"}]
 *         ),
 *       });
 *       this.selector.on("select2:select", (event) => {
 *         // select2 => Alpine signals here
 *         this.currentSelect = this.selector.select2("data")
 *       });
 *       this.$watch("currentSelected" (value) => {
 *          // Alpine => select2 signals here
 *       });
 *     },
 *   }));
 * })
 * </script>
 */

import type {
  AjaxOptions,
  DataFormat,
  GroupedDataFormat,
  LoadingData,
  Options,
} from "select2";
import "select2/dist/css/select2.css";

export interface Select2Object {
  id: number;
  text: string;
}

// biome-ignore lint/suspicious/noExplicitAny: You have to do it at some point
export type RemoteResult = any;
export type AjaxResponse = AjaxOptions<DataFormat | GroupedDataFormat, RemoteResult>;

interface DataSource {
  ajax?: AjaxResponse | undefined;
  data?: RemoteResult | DataFormat[] | GroupedDataFormat[] | undefined;
}

interface Select2Options {
  element: Element;
  /** the data source, built with `localDataSource` or `remoteDataSource` */
  dataSource: DataSource;
  excluded?: number[];
  /** A callback to get the picture field from the API response */
  pictureGetter?: (element: LoadingData | DataFormat | GroupedDataFormat) => string;
  /** Any other select2 parameter to apply on the config */
  overrides?: Options;
}

/**
 * Create a new select2 with sith presets
 */
export function sithSelect2(options: Select2Options) {
  const elem = $(options.element as HTMLInputElement);
  return elem.select2({
    theme: elem[0].multiple ? "classic" : "default",
    minimumInputLength: 2,
    templateResult: selectItemBuilder(options.pictureGetter),
    ...options.dataSource,
    ...(options.overrides ?? {}),
  });
}

interface LocalSourceOptions {
  excluded: () => number[];
}

/**
 * Build a data source for a Select2 from a local array
 */
export function localDataSource(
  source: Select2Object[] /** Array containing the data */,
  options: LocalSourceOptions,
): DataSource {
  if (options.excluded) {
    const ids = options.excluded();
    return { data: source.filter((i) => !ids.includes(i.id)) };
  }
  return { data: source };
}

interface RemoteSourceOptions {
  /** A callback to the ids to exclude from the search */
  excluded?: () => number[];
  /** A converter for a value coming from the remote api */
  resultConverter?: ((obj: RemoteResult) => DataFormat | GroupedDataFormat) | undefined;
  /** Any other select2 parameter to apply on the config */
  overrides?: AjaxOptions;
}

/**
 * Build a data source for a Select2 from a remote url
 */
export function remoteDataSource(
  source: string /** url of the endpoint */,
  options: RemoteSourceOptions,
): DataSource {
  $.ajaxSetup({
    traditional: true,
  });
  const params: AjaxOptions = {
    url: source,
    dataType: "json",
    cache: true,
    delay: 250,
    data: function (params) {
      return {
        search: params.term,
        exclude: [
          ...(this.val() || []).map((i: string) => Number.parseInt(i)),
          ...(options.excluded ? options.excluded() : []),
        ],
      };
    },
  };
  if (options.resultConverter) {
    params.processResults = (data) => ({
      results: data.results.map(options.resultConverter),
    });
  }
  if (options.overrides) {
    Object.assign(params, options.overrides);
  }
  return { ajax: params };
}

export function itemFormatter(user: { loading: boolean; text: string }) {
  if (user.loading) {
    return user.text;
  }
}

/**
 * Build a function to display the results
 */
export function selectItemBuilder(pictureGetter?: (item: RemoteResult) => string) {
  return (item: RemoteResult) => {
    const picture = typeof pictureGetter === "function" ? pictureGetter(item) : null;
    const wrapper = document.createElement("div");
    wrapper.classList.add("select-item");
    if (picture) {
      const img = document.createElement("img");
      img.src = picture;
      img.alt = encodeURI(item.text);
      img.onerror = () => {
        img.src = "/static/core/img/unknown.jpg";
      };
      wrapper.appendChild(img);
    }
    const textSpan = document.createElement("span");
    textSpan.classList.add("select-item-text");
    textSpan.appendChild(document.createTextNode(item.text));
    wrapper.appendChild(textSpan);

    return $(wrapper);
  };
}
