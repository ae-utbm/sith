$(document).ready(function(){

    $("#poster_list #view").click(function(e){
        $("#view").removeClass("active");
    });

    $("#poster_list .poster").click(function(e){

        el = $(e.target);
        $("#poster_list #view #placeholder").html(el);

        $("#view").addClass("active");
    });

    $(document).keyup(function(e) {
        if (e.keyCode == 27) { // escape key maps to keycode `27`
            e.preventDefault();
            $("#view").removeClass("active");
        }
    });

});
