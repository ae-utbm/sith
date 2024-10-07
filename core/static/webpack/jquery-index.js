import $ from "jquery";
import "jquery.shorten/src/jquery.shorten.min.js";

// We ship jquery-ui with jquery because when standalone with webpack
// JQuery is also included in the jquery-ui package. We do gain space by doing this
// We require jquery-ui components manually and not in a loop
// Otherwise it increases the output files by a x2 factor !
require("jquery-ui/ui/widgets/accordion.js");
require("jquery-ui/ui/widgets/autocomplete.js");
require("jquery-ui/ui/widgets/button.js");
require("jquery-ui/ui/widgets/dialog.js");
require("jquery-ui/ui/widgets/tabs.js");

require("jquery-ui/themes/base/all.css");

/**
 * Simple wrapper to solve shorten not being able on legacy pages
 * @param {string} selector to be passed to jQuery
 * @param {Object} options object to pass to the shorten function
 **/
function shorten(selector, options) {
	$(selector).shorten(options);
}

window.shorten = shorten;
