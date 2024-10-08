// biome-ignore lint/correctness/noUnusedVariables: used in user_edit.jinja
function alpineWebcamBuilder(defaultPicture, deleteUrl, canDeletePicture) {
  return () => ({
    canEditPicture: false,

    loading: false,
    isCameraEnabled: false,
    isCameraError: false,
    picture: null,
    video: null,
    pictureForm: null,

    init() {
      this.video = this.$refs.video;
      this.pictureForm = this.$refs.form.getElementsByTagName("input");
      if (this.pictureForm.length > 0) {
        this.pictureForm = this.pictureForm[0];
        this.canEditPicture = true;

        // Link the displayed element to the form input
        this.pictureForm.onchange = (event) => {
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

    getPicture() {
      return this.picture || defaultPicture;
    },

    deletePicture() {
      // Only remove currently displayed picture
      if (this.picture) {
        const list = new DataTransfer();
        this.pictureForm.files = list.files;
        this.pictureForm.dispatchEvent(new Event("change"));
        return;
      }
      if (!canDeletePicture) {
        return;
      }
      // Remove user picture if correct rights are available
      window.open(deleteUrl, "_self");
    },

    enableCamera() {
      this.picture = null;
      this.loading = true;
      this.isCameraError = false;
      navigator.mediaDevices
        .getUserMedia({ video: true, audio: false })
        .then((stream) => {
          this.loading = false;
          this.isCameraEnabled = true;
          this.video.srcObject = stream;
          this.video.play();
        })
        .catch((err) => {
          this.isCameraError = true;
          this.loading = false;
          throw err;
        });
    },

    takePicture() {
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
        this.pictureForm.files = list.files;

        // No change event is triggered, we trigger it manually #}
        this.pictureForm.dispatchEvent(new Event("change"));
      }, "image/webp");

      canvas.remove();
      this.isCameraEnabled = false;
    },
  });
}
