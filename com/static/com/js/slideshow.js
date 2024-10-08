$(document).ready(() => {
  transition_time = 1000;

  i = 0;
  max = $("#slideshow .slide").length;

  next_trigger = 0;

  function enterFullscreen() {
    element = document.getElementById("slideshow");
    $(element).addClass("fullscreen");
    if (element.requestFullscreen) {
      element.requestFullscreen();
    } else if (element.mozRequestFullScreen) {
      element.mozRequestFullScreen();
    } else if (element.webkitRequestFullscreen) {
      element.webkitRequestFullscreen();
    } else if (element.msRequestFullscreen) {
      element.msRequestFullscreen();
    }
  }

  function exitFullscreen() {
    element = document.getElementById("slideshow");
    $(element).removeClass("fullscreen");
    if (document.exitFullscreen) {
      document.exitFullscreen();
    } else if (document.webkitExitFullscreen) {
      document.webkitExitFullscreen();
    } else if (document.mozCancelFullScreen) {
      document.mozCancelFullScreen();
    } else if (document.msExitFullscreen) {
      document.msExitFullscreen();
    }
  }

  function init_progress_bar() {
    $("#slideshow #progress_bar").css("transition", "none");
    $("#slideshow #progress_bar").removeClass("progress");
    $("#slideshow #progress_bar").addClass("init");
  }

  function start_progress_bar(display_time) {
    $("#slideshow #progress_bar").removeClass("init");
    $("#slideshow #progress_bar").addClass("progress");
    $("#slideshow #progress_bar").css("transition", `width ${display_time}s linear`);
  }

  function next() {
    init_progress_bar();
    slide = $($("#slideshow .slide").get(i % max));
    slide.removeClass("center");
    slide.addClass("left");

    next_slide = $($("#slideshow .slide").get((i + 1) % max));
    next_slide.removeClass("right");
    next_slide.addClass("center");
    display_time = next_slide.attr("display_time") || 2;

    $("#slideshow .bullet").removeClass("active");
    bullet = $("#slideshow .bullet")[(i + 1) % max];
    $(bullet).addClass("active");

    i = (i + 1) % max;

    setTimeout(() => {
      others_left = $("#slideshow .slide.left");
      others_left.removeClass("left");
      others_left.addClass("right");

      start_progress_bar(display_time);
      next_trigger = setTimeout(next, display_time * 1000);
    }, transition_time);
  }

  display_time = $("#slideshow .center").attr("display_time");
  init_progress_bar();
  setTimeout(() => {
    if (max > 1) {
      start_progress_bar(display_time);
      setTimeout(next, display_time * 1000);
    }
  }, 10);

  $("#slideshow").click((e) => {
    if (!$("#slideshow").hasClass("fullscreen")) {
      console.log("Entering fullscreen ...");
      enterFullscreen();
    } else {
      console.log("Exiting fullscreen ...");
      exitFullscreen();
    }
  });

  $(document).keyup((e) => {
    if (e.keyCode === 27) {
      // escape key maps to keycode `27`
      e.preventDefault();
      console.log("Exiting fullscreen ...");
      exitFullscreen();
    }
  });
});
