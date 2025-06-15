$(() => {
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
