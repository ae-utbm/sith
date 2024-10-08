$(document).ready(() => {
  const transitionTime = 1000;

  let i = 0;
  const max = $("#slideshow .slide").length;

  function enterFullscreen() {
    const element = document.getElementById("slideshow");
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
    const element = document.getElementById("slideshow");
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

  function initProgressBar() {
    $("#slideshow #progress_bar").css("transition", "none");
    $("#slideshow #progress_bar").removeClass("progress");
    $("#slideshow #progress_bar").addClass("init");
  }

  function startProgressBar(displayTime) {
    $("#slideshow #progress_bar").removeClass("init");
    $("#slideshow #progress_bar").addClass("progress");
    $("#slideshow #progress_bar").css("transition", `width ${displayTime}s linear`);
  }

  function next() {
    initProgressBar();
    const slide = $($("#slideshow .slide").get(i % max));
    slide.removeClass("center");
    slide.addClass("left");

    const nextSlide = $($("#slideshow .slide").get((i + 1) % max));
    nextSlide.removeClass("right");
    nextSlide.addClass("center");
    const displayTime = nextSlide.attr("display_time") || 2;

    $("#slideshow .bullet").removeClass("active");
    const bullet = $("#slideshow .bullet")[(i + 1) % max];
    $(bullet).addClass("active");

    i = (i + 1) % max;

    setTimeout(() => {
      const othersLeft = $("#slideshow .slide.left");
      othersLeft.removeClass("left");
      othersLeft.addClass("right");

      startProgressBar(displayTime);
      setTimeout(next, displayTime * 1000);
    }, transitionTime);
  }

  const displayTime = $("#slideshow .center").attr("display_time");
  initProgressBar();
  setTimeout(() => {
    if (max > 1) {
      startProgressBar(displayTime);
      setTimeout(next, displayTime * 1000);
    }
  }, 10);

  $("#slideshow").click(() => {
    if ($("#slideshow").hasClass("fullscreen")) {
      exitFullscreen();
    } else {
      enterFullscreen();
    }
  });

  $(document).keyup((e) => {
    if (e.keyCode === 27) {
      // escape key maps to keycode `27`
      e.preventDefault();
      exitFullscreen();
    }
  });
});
