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
    },
    buttons: [
      {
        text: "Choose",
        click: function () {
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
      popup.html(
        '<iframe src="/file/popup" width="100%" height="95%"></iframe><div id="file_id" value="null" />',
      );
      popup.dialog({ title: $(this).text() }).dialog("open");
    });
  $("#quick_notif li").click(function () {
    $(this).hide();
  });
});

// biome-ignore lint/correctness/noUnusedVariables: used in other scripts
function createQuickNotif(msg) {
  const el = document.createElement("li");
  el.textContent = msg;
  el.addEventListener("click", () => el.parentNode.removeChild(el));
  document.getElementById("quick_notif").appendChild(el);
}

// biome-ignore lint/correctness/noUnusedVariables: used in other scripts
function deleteQuickNotifs() {
  const el = document.getElementById("quick_notif");
  while (el.firstChild) {
    el.removeChild(el.firstChild);
  }
}

// biome-ignore lint/correctness/noUnusedVariables: used in other scripts
function displayNotif() {
  $("#header_notif").toggle().parent().toggleClass("white");
}

// You can't get the csrf token from the template in a widget
// We get it from a cookie as a workaround, see this link
// https://docs.djangoproject.com/en/2.0/ref/csrf/#ajax
// Sadly, getting the cookie is not possible with CSRF_COOKIE_HTTPONLY or CSRF_USE_SESSIONS is True
// So, the true workaround is to get the token from the dom
// https://docs.djangoproject.com/en/2.0/ref/csrf/#acquiring-the-token-if-csrf-use-sessions-is-true
// biome-ignore lint/style/useNamingConvention: can't find it used anywhere but I will not play with the devil
// biome-ignore lint/correctness/noUnusedVariables: used in other scripts
function getCSRFToken() {
  return $("[name=csrfmiddlewaretoken]").val();
}
