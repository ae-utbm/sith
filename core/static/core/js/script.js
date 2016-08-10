console.log('Guy');

$( function() {
    dialog = $( ".choose_file_widget" ).dialog({
        autoOpen: false,
        modal: true,
    });
    $( ".choose_file_button" ).button().on( "click", function() {
        dialog.dialog( "open" );
    });
} );
