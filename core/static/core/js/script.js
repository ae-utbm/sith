console.log('Guy');

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
} );

function display_notif() {
    $('#header_notif').toggle().parent().toggleClass("white");
}

// You can't get the csrf token from the template in a widget
// We get it from a cookie as a workaround, see this link
// https://docs.djangoproject.com/en/2.0/ref/csrf/#ajax
function getCookie(cname) {
    var name = cname + "=";
    var decodedCookie = decodeURIComponent(document.cookie);
    var ca = decodedCookie.split(';');
    for(var i = 0; i <ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}