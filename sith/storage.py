import logging

import rjsmin
import sass
from django.conf import settings
from django.contrib.staticfiles.storage import (
    ManifestStaticFilesStorage,
)
from django.core.files.storage import Storage


class SithStorage(ManifestStaticFilesStorage):
    def _compile_scss(self):
        to_exec = list(settings.STATIC_ROOT.rglob("*.scss"))
        if len(to_exec) == 0:
            return
        for file in to_exec:
            # remove existing css files that will be replaced
            # keeping them while compiling the scss would break
            # import statements resolution
            css_file = file.with_suffix(".css")
            if css_file.exists():
                css_file.unlink()
        scss_paths = [p.resolve() for p in to_exec if p.suffix == ".scss"]
        base_args = {"output_style": "compressed", "precision": settings.SASS_PRECISION}
        compiled_files = {
            p: sass.compile(filename=str(p), **base_args) for p in scss_paths
        }
        for file, scss in compiled_files.items():
            file.replace(file.with_suffix(".css")).write_text(scss)

        # once the files are compiled, the manifest must be updated
        # to have the right suffix
        new_entries = {
            k.replace(".scss", ".css"): self.hashed_files.pop(k).replace(
                ".scss", ".css"
            )
            for k in list(self.hashed_files.keys())
            if k.endswith(".scss")
        }
        self.hashed_files.update(new_entries)
        self.save_manifest()

    @staticmethod
    def _minify_js():
        to_exec = [
            p for p in settings.STATIC_ROOT.rglob("*.js") if ".min" not in p.suffixes
        ]
        for path in to_exec:
            p = path.resolve()
            minified = rjsmin.jsmin(p.read_text())
            p.write_text(minified)
            logging.getLogger("main").info(f"Minified {path}")

    def post_process(
        self, paths: dict[str, tuple[Storage, str]], *, dry_run: bool = False
    ):
        # Whether we get the files that were processed by ManifestFilesMixin
        # by calling super() or whether we get them from the manifest file
        # makes no difference - we have to open the manifest file anyway
        # because we need to update the paths stored inside it.
        yield from super().post_process(paths, dry_run)

        self._compile_scss()
        self._minify_js()
