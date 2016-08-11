console.log('Guy');

$( function() {
    buttons = $(".choose_file_button");
    popups = $(".choose_file_widget");
    popups.dialog({
        autoOpen: false,
        modal: true,
        width: "80%",
        minHeight: "300",
        buttons: {
            "Choose": function() {
                console.log($("#file_id"));
                $("input[name="+$(this).attr('name')+"]").attr('value', $("#file_id").attr('value'));
                $( this ).dialog( "close" );
            }
        }
    });
    $('.select_date').datepicker({
        changeMonth: true,
        changeYear: true
    });
    $( ".choose_file_button" ).button().on( "click", function() {
        popup = popups.filter("[name="+$(this).attr('name')+"]");
        console.log(popup);
        popup.html('<iframe src="/file/popup" width="95%"></iframe><span id="file_id" value="null" />');
        popup.dialog({title: $(this).attr('name')}).dialog( "open" );
    });
} );
