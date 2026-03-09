import { paginated } from "#core:utils/api.ts";
import { History, initialUrlParams, updateQueryString } from "#core:utils/history.ts";
import {
  type AlbumFetchAlbumData,
  type AlbumSchema,
  albumFetchAlbum,
  type PictureSchema,
  type PicturesFetchPicturesData,
  type PicturesUploadPictureErrors,
  picturesFetchPictures,
  picturesUploadPicture,
} from "#openapi";

interface AlbumPicturesConfig {
  albumId: number;
  maxPageSize: number;
}

interface SubAlbumsConfig {
  parentId: number;
}

document.addEventListener("alpine:init", () => {
  Alpine.data("pictures", (config: AlbumPicturesConfig) => ({
    pictures: [] as PictureSchema[],
    page: Number.parseInt(initialUrlParams.get("page"), 10) || 1,
    pushstate: History.Push /* Used to avoid pushing a state on a back action */,
    loading: false,

    async init() {
      await this.fetchPictures();
      this.$watch("page", () => {
        updateQueryString("page", this.page === 1 ? null : this.page, this.pushstate);
        this.pushstate = History.Push;
        this.fetchPictures();
      });

      window.addEventListener("popstate", () => {
        this.pushstate = History.Replace;
        this.page =
          Number.parseInt(
            new URLSearchParams(window.location.search).get("page"),
            10,
          ) || 1;
      });
    },

    getPage(page: number) {
      return this.pictures.slice(
        (page - 1) * config.maxPageSize,
        config.maxPageSize * page,
      );
    },

    async fetchPictures() {
      this.loading = true;
      this.pictures = await paginated(picturesFetchPictures, {
        // biome-ignore lint/style/useNamingConvention: API is in snake_case
        query: { album_id: config.albumId },
      } as PicturesFetchPicturesData);
      this.loading = false;
    },

    nbPages() {
      return Math.ceil(this.pictures.length / config.maxPageSize);
    },
  }));

  Alpine.data("albums", (config: SubAlbumsConfig) => ({
    albums: [] as AlbumSchema[],
    loading: false,

    async init() {
      await this.fetchAlbums();
    },

    async fetchAlbums() {
      this.loading = true;
      this.albums = await paginated(albumFetchAlbum, {
        // biome-ignore lint/style/useNamingConvention: API is snake_case
        query: { parent_id: config.parentId },
      } as AlbumFetchAlbumData);
      this.loading = false;
    },
  }));

  Alpine.data("pictureUpload", (albumId: number) => ({
    errors: [] as string[],
    sending: false,
    progress: null as HTMLProgressElement,

    init() {
      this.progress = this.$refs.progress;
    },

    async sendPictures() {
      const input = this.$refs.pictures as HTMLInputElement;
      const files = input.files;
      this.errors = [];
      this.progress.value = 0;
      this.progress.max = files.length;
      this.sending = true;
      for (const file of files) {
        await this.sendPicture(file);
      }
      this.sending = false;
      // This should trigger a reload of the pictures of the `picture` Alpine data
      this.$dispatch("pictures-upload-done");
    },

    async sendPicture(file: File) {
      const res = await picturesUploadPicture({
        // biome-ignore lint/style/useNamingConvention: api is snake_case
        body: { album_id: albumId, picture: file },
      });
      if (!res.response.ok) {
        let msg = "";
        if (res.response.status === 422) {
          msg = (res.error as PicturesUploadPictureErrors[422]).detail
            .map((err: Record<"ctx", Record<"error", string>>) => err.ctx.error)
            .join(" ; ");
        } else {
          msg = Object.values(res.error.detail).join(" ; ");
        }
        this.errors.push(`${file.name} : ${msg}`);
      }
      this.progress.value += 1;
    },
  }));
});

// Todo: migrate to alpine.js if we have some time
// $("form#upload_form").submit(function (event) {
//   const formData = new FormData($(this)[0]);
//
//   if (!formData.get("album_name") && !formData.get("images").name) return false;
//
//   if (!formData.get("images").name) {
//     return true;
//   }
//
//   event.preventDefault();
//
//   let errorList = this.querySelector("#upload_form ul.errorlist.nonfield");
//   if (errorList === null) {
//     errorList = document.createElement("ul");
//     errorList.classList.add("errorlist", "nonfield");
//     this.insertBefore(errorList, this.firstElementChild);
//   }
//
//   while (errorList.childElementCount > 0)
//     errorList.removeChild(errorList.firstElementChild);
//
//   let progress = this.querySelector("progress");
//   if (progress === null) {
//     progress = document.createElement("progress");
//     progress.value = 0;
//     const p = document.createElement("p");
//     p.appendChild(progress);
//     this.insertBefore(p, this.lastElementChild);
//   }
//
//   let dataHolder;
//
//   if (formData.get("album_name")) {
//     dataHolder = new FormData();
//     dataHolder.set("csrfmiddlewaretoken", "{{ csrf_token }}");
//     dataHolder.set("album_name", formData.get("album_name"));
//     $.ajax({
//       method: "POST",
//       url: "{{ url('sas:album_upload', album_id=object.id) }}",
//       data: dataHolder,
//       processData: false,
//       contentType: false,
//       success: onSuccess,
//     });
//   }
//
//   const images = formData.getAll("images");
//   const imagesCount = images.length;
//   let completeCount = 0;
//
//   const poolSize = 1;
//   const imagePool = [];
//
//   while (images.length > 0 && imagePool.length < poolSize) {
//     const image = images.shift();
//     imagePool.push(image);
//     sendImage(image);
//   }
//
//   function sendImage(image) {
//     dataHolder = new FormData();
//     dataHolder.set("csrfmiddlewaretoken", "{{ csrf_token }}");
//     dataHolder.set("images", image);
//
//     $.ajax({
//       method: "POST",
//       url: "{{ url('sas:album_upload', album_id=object.id) }}",
//       data: dataHolder,
//       processData: false,
//       contentType: false,
//     })
//       .fail(onSuccess.bind(undefined, image))
//       .done(onSuccess.bind(undefined, image))
//       .always(next.bind(undefined, image));
//   }
//
//   function next(image, _, __) {
//     const index = imagePool.indexOf(image);
//     const nextImage = images.shift();
//
//     if (index !== -1) {
//       imagePool.splice(index, 1);
//     }
//
//     if (nextImage) {
//       imagePool.push(nextImage);
//       sendImage(nextImage);
//     }
//   }
//
//   function onSuccess(image, data, _, __) {
//     let errors = [];
//
//     if ($(data.responseText).find(".errorlist.nonfield")[0])
//       errors = Array.from($(data.responseText).find(".errorlist.nonfield")[0].children);
//
//     while (errors.length > 0) errorList.appendChild(errors.shift());
//
//     progress.value = ++completeCount / imagesCount;
//     if (progress.value === 1 && errorList.children.length === 0)
//       document.location.reload();
//   }
// });
