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
 *   data_source: local_data_source(data)
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
 *   data_source: local_data_source(data, {
 *     excluded: () => data.filter((i) => i.text === "to exclude").map((i) => parseInt(i))
 *   })
 * }));
 * ```
 *
 * # Remote data source
 *
 * Select2 with remote data sources are similar to those with local
 * data, but with some more parameters, like `result_converter`,
 * which takes a callback that must return a `Select2Object`.
 *
 * ```js
 * document.addEventListener("DOMContentLoaded", () => sithSelect2({
 *   element: document.getElementById("select2-input"),
 *   data_source: remote_data_source("/api/user/search", {
 *     excluded: () => [1, 2],  // exclude users 1 and 2 from the search
 *     result_converter: (user) => Object({id: user.id, text: user.first_name})
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
 * document.addEventListener("DOMContentLoaded", () => sithSelect2({
 *   element: document.getElementById("select2-input"),
 *   data_source: remote_data_source("/api/user/search", {
 *     result_converter: (user) => Object({id: user.id, text: user.first_name}),
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
 * In this case, fill the `picture_getter` option :
 *
 * ```js
 * document.addEventListener("DOMContentLoaded", () => sithSelect2({
 *   element: document.getElementById("select2-input"),
 *   data_source: remote_data_source("/api/user/search", {
 *     result_converter: (user) => Object({id: user.id, text: user.first_name})
 *   })
 *   picture_getter: (user) => user.profile_pict,
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
 *     <p x-text="current_selection.id"></p>
 *     <p x-text="current_selection.text"></p>
 *   </div>
 * </body>
 *
 * <script>
 * document.addEventListener("alpine:init", () => {
 *   Alpine.data("select2_test", () => ({
 *     selector: undefined,
 *     current_select: {id: "", text: ""},
 *
 *     init() {
 *       this.selector = sithSelect2({
 *         element: $(this.$refs.select),
 *         data_source: local_data_source(
 *           [{id: 1, text: "foo"}, {id: 2, text: "bar"}]
 *         ),
 *       });
 *       this.selector.on("select2:select", (event) => {
 *         // select2 => Alpine signals here
 *         this.current_select = this.selector.select2("data")
 *       });
 *       this.$watch("current_selected" (value) => {
 *          // Alpine => select2 signals here
 *       });
 *     },
 *   }));
 * })
 * </script>
 */

/**
 * @typedef Select2Object
 * @property {number} id
 * @property {string} text
 */

/**
 * @typedef Select2Options
 * @property {Element} element
 * @property {Object} data_source
 *      the data source, built with `local_data_source` or `remote_data_source`
 * @property {number[]} excluded A list of ids to exclude from search
 * @property {undefined | function(Object): string} picture_getter
 *      A callback to get the picture field from the API response
 * @property {Object | undefined} overrides
 *      Any other select2 parameter to apply on the config
 */

/**
 * @param {Select2Options} options
 */
function sithSelect2(options) {
  const elem = $(options.element);
  return elem.select2({
    theme: elem[0].multiple ? "classic" : "default",
    minimumInputLength: 2,
    templateResult: select_item_builder(options.picture_getter),
    ...options.data_source,
    ...(options.overrides || {}),
  });
}

/**
 * @typedef LocalSourceOptions
 * @property {undefined | function(): number[]} excluded
 *        A callback to the ids to exclude from the search
 */

/**
 * Build a data source for a Select2 from a local array
 * @param {Select2Object[]} source The array containing the data
 * @param {RemoteSourceOptions} options
 */
function local_data_source(source, options) {
  if (options.excluded) {
    const ids = options.excluded();
    return { data: source.filter((i) => !ids.includes(i.id)) };
  }
  return { data: source };
}

/**
 * @typedef RemoteSourceOptions
 * @property {undefined | function(): number[]} excluded
 *     A callback to the ids to exclude from the search
 * @property {undefined | function(): Select2Object} result_converter
 *     A converter for a value coming from the remote api
 * @property {undefined | Object} overrides
 *     Any other select2 parameter to apply on the config
 */

/**
 * Build a data source for a Select2 from a remote url
 * @param {string} source The url of the endpoint
 * @param {RemoteSourceOptions} options
 */
function remote_data_source(source, options) {
  jQuery.ajaxSettings.traditional = true;
  const params = {
    url: source,
    dataType: "json",
    cache: true,
    delay: 250,
    data: function (params) {
      return {
        search: params.term,
        exclude: [
          ...(this.val() || []).map((i) => Number.parseInt(i)),
          ...(options.excluded ? options.excluded() : []),
        ],
      };
    },
  };
  if (options.result_converter) {
    params.processResults = (data) => ({
      results: data.results.map(options.result_converter),
    });
  }
  if (options.overrides) {
    Object.assign(params, options.overrides);
  }
  return { ajax: params };
}

function item_formatter(user) {
  if (user.loading) {
    return user.text;
  }
}

/**
 * Build a function to display the results
 * @param {null | function(Object):string} picture_getter
 * @return {function(string): jQuery|HTMLElement}
 */
function select_item_builder(picture_getter) {
  return (item) => {
    const picture = typeof picture_getter === "function" ? picture_getter(item) : null;
    const img_html = picture
      ? `<img 
          src="${picture_getter(item)}" 
          alt="${item.text}" 
          onerror="this.src = '/static/core/img/unknown.jpg'" 
        />`
      : "";

    return $(`<div class="select-item">
        ${img_html}
         <span class="select-item-text">${item.text}</span>
         </div>`);
  };
}
