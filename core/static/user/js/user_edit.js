function alpine_webcam_builder(default_picture, delete_url, can_delete_picture) {
  return () => ({
    can_edit_picture: false,

    loading: false,
    is_camera_enabled: false,
    is_camera_error: false,
    picture: null,
    video: null,
    picture_form: null,

    init() {
      this.video = this.$refs.video;
      this.picture_form = this.$refs.form.getElementsByTagName("input");
      if (this.picture_form.length > 0) {
        this.picture_form = this.picture_form[0];
        this.can_edit_picture = true;

        // Link the displayed element to the form input
        this.picture_form.onchange = (event) => {
          const files = event.srcElement.files;
          if (files.length > 0) {
            this.picture = (window.URL || window.webkitURL).createObjectURL(
              event.srcElement.files[0],
            );
          } else {
            this.picture = null;
          }
        };
      }
    },

    get_picture() {
      return this.picture || default_picture;
    },

    delete_picture() {
      // Only remove currently displayed picture
      if (this.picture) {
        const list = new DataTransfer();
        this.picture_form.files = list.files;
        this.picture_form.dispatchEvent(new Event("change"));
        return;
      }
      if (!can_delete_picture) {
        return;
      }
      // Remove user picture if correct rights are available
      window.open(delete_url, "_self");
    },

    enable_camera() {
      this.picture = null;
      this.loading = true;
      this.is_camera_error = false;
      navigator.mediaDevices
        .getUserMedia({ video: true, audio: false })
        .then((stream) => {
          this.loading = false;
          this.is_camera_enabled = true;
          this.video.srcObject = stream;
          this.video.play();
        })
        .catch((err) => {
          this.is_camera_error = true;
          this.loading = false;
          throw err;
        });
    },

    take_picture() {
      const canvas = document.createElement("canvas");
      const context = canvas.getContext("2d");

      /* Create the image */
      const settings = this.video.srcObject.getTracks()[0].getSettings();
      canvas.width = settings.width;
      canvas.height = settings.height;
      context.drawImage(this.video, 0, 0, canvas.width, canvas.height);

      /* Stop camera */
      this.video.pause();
      for (const track of this.video.srcObject.getTracks()) {
        if (track.readyState === "live") {
          track.stop();
        }
      }

      canvas.toBlob((blob) => {
        const filename = interpolate(gettext("captured.%s"), ["webp"]);
        const file = new File([blob], filename, {
          type: "image/webp",
        });

        const list = new DataTransfer();
        list.items.add(file);
        this.picture_form.files = list.files;

        // No change event is triggered, we trigger it manually #}
        this.picture_form.dispatchEvent(new Event("change"));
      }, "image/webp");

      canvas.remove();
      this.is_camera_enabled = false;
    },
  });
}
