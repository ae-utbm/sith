$(() => {
  // const buttons = $('.choose_file_button')
  const popups = $(".choose_file_widget");
  popups.dialog({
    autoOpen: false,
    modal: true,
    width: "90%",
    create: (event) => {
      const target = $(event.target);
      target.parent().css({
        position: "fixed",
        top: "5%",
        bottom: "5%",
      });
      target.css("height", "300px");
      console.log(target);
    },
    buttons: [
      {
        text: "Choose",
        click: function () {
          console.log($("#file_id"));
          $(`input[name=${$(this).attr("name")}]`).attr(
            "value",
            $("#file_id").attr("value"),
          );
          $(this).dialog("close");
        },
        disabled: true,
      },
    ],
  });
  $(".choose_file_button")
    .button()
    .on("click", function () {
      const popup = popups.filter(`[name=${$(this).attr("name")}]`);
      console.log(popup);
      popup.html(
        '<iframe src="/file/popup" width="100%" height="95%"></iframe><div id="file_id" value="null" />',
      );
      popup.dialog({ title: $(this).text() }).dialog("open");
    });
  $("#quick_notif li").click(function () {
    $(this).hide();
  });
});

function createQuickNotif(msg) {
  const el = document.createElement("li");
  el.textContent = msg;
  el.addEventListener("click", () => el.parentNode.removeChild(el));
  document.getElementById("quick_notif").appendChild(el);
}

function deleteQuickNotifs() {
  const el = document.getElementById("quick_notif");
  while (el.firstChild) {
    el.removeChild(el.firstChild);
  }
}

function display_notif() {
  $("#header_notif").toggle().parent().toggleClass("white");
}

// You can't get the csrf token from the template in a widget
// We get it from a cookie as a workaround, see this link
// https://docs.djangoproject.com/en/2.0/ref/csrf/#ajax
// Sadly, getting the cookie is not possible with CSRF_COOKIE_HTTPONLY or CSRF_USE_SESSIONS is True
// So, the true workaround is to get the token from the dom
// https://docs.djangoproject.com/en/2.0/ref/csrf/#acquiring-the-token-if-csrf-use-sessions-is-true
function getCSRFToken() {
  return $("[name=csrfmiddlewaretoken]").val();
}

const initialUrlParams = new URLSearchParams(window.location.search);

/**
 * @readonly
 * @enum {number}
 */
const History = {
  NONE: 0,
  PUSH: 1,
  REPLACE: 2,
};

/**
 * @param {string} key
 * @param {string | string[] | null} value
 * @param {History} action
 * @param {URL | null} url
 */
function update_query_string(key, value, action = History.REPLACE, url = null) {
  let ret = url;
  if (!ret) {
    ret = new URL(window.location.href);
  }
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

  if (action === History.PUSH) {
    window.history.pushState(null, "", ret.toString());
  } else if (action === History.REPLACE) {
    window.history.replaceState(null, "", ret.toString());
  }

  return ret;
}

// TODO : If one day a test workflow is made for JS in this project
//  please test this function. A all cost.
/**
 * Given a paginated endpoint, fetch all the items of this endpoint,
 * performing multiple API calls if necessary.
 * @param {string} url The paginated endpoint to fetch
 * @return {Promise<Object[]>}
 */
async function fetch_paginated(url) {
  const max_per_page = 199;
  const paginated_url = new URL(url, document.location.origin);
  paginated_url.searchParams.set("page_size", max_per_page.toString());
  paginated_url.searchParams.set("page", "1");

  const first_page = await (await fetch(paginated_url)).json();
  const results = first_page.results;

  const nb_pictures = first_page.count;
  const nb_pages = Math.ceil(nb_pictures / max_per_page);

  if (nb_pages > 1) {
    const promises = [];
    for (let i = 2; i <= nb_pages; i++) {
      paginated_url.searchParams.set("page", i.toString());
      promises.push(
        fetch(paginated_url).then((res) => res.json().then((json) => json.results)),
      );
    }
    results.push(...(await Promise.all(promises)).flat());
  }
  return results;
}
