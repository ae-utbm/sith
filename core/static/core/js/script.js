$( function() {
    buttons = $(".choose_file_button");
    popups = $(".choose_file_widget");
    popups.dialog({
        autoOpen: false,
        modal: true,
        width: "90%",
        create: function (event) {
            target = $(event.target);
            target.parent().css({
                'position': 'fixed',
                'top': '5%',
                'bottom': '5%',
            });
            target.css("height", "300px");
            console.log(target);
        },
        buttons: [
        {
            text: "Choose",
            click: function() {
                console.log($("#file_id"));
                $("input[name="+$(this).attr('name')+"]").attr('value', $("#file_id").attr('value'));
                $( this ).dialog( "close" );
            },
            disabled: true,
        }
        ],
    });
    $( ".choose_file_button" ).button().on( "click", function() {
        popup = popups.filter("[name="+$(this).attr('name')+"]");
        console.log(popup);
        popup.html('<iframe src="/file/popup" width="100%" height="95%"></iframe><div id="file_id" value="null" />');
        popup.dialog({title: $(this).text()}).dialog( "open" );
    });
    $("#quick_notif li").click(function () {
        $(this).hide();
    })
});

function createQuickNotif(msg) {
    const el = document.createElement('li')
    el.textContent = msg
    el.addEventListener('click', () => el.parentNode.removeChild(el))
    document.getElementById('quick_notif').appendChild(el)
}

function deleteQuickNotifs() {
    const el = document.getElementById('quick_notif')
    while (el.firstChild) {
        el.removeChild(el.firstChild)
    }
}

function display_notif() {
    $('#header_notif').toggle().parent().toggleClass("white");
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
    if (!url){
        url = new URL(window.location.href);
    }
    if (value === null || value === "") {
        // If the value is null, undefined or empty => delete it
        url.searchParams.delete(key)
    } else if (Array.isArray(value)) {
        url.searchParams.delete(key)
        value.forEach((v) => url.searchParams.append(key, v))
    } else {
        url.searchParams.set(key, value);
    }

    if (action === History.PUSH) {
        history.pushState(null, "", url.toString());
    } else if (action === History.REPLACE) {
        history.replaceState(null, "", url.toString());
    }

    return url;
}
