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
} );

function display_notif() {
    $('#notif').toggle();
}
