$(document).ready(() => {
	$("#poster_list #view").click((e) => {
		$("#view").removeClass("active");
	});

	$("#poster_list .poster .image").click((e) => {
		let el = $(e.target);
		if (el.hasClass("image")) {
			el = el.find("img");
		}
		$("#poster_list #view #placeholder").html(el.clone());

		$("#view").addClass("active");
	});

	$(document).keyup((e) => {
		if (e.keyCode === 27) {
			// escape key maps to keycode `27`
			e.preventDefault();
			$("#view").removeClass("active");
		}
	});
});
