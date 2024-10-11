from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles.finders import find
from django.contrib.staticfiles.storage import (
    ManifestStaticFilesStorage,
)
from django.core.files.storage import Storage

from staticfiles.processors import JS, Scss


class ManifestPostProcessingStorage(ManifestStaticFilesStorage):
    def url(self, name: str, *, force: bool = False) -> str:
        """Get the URL for a file, convert .scss calls to .css ones and .ts to .js"""
        # This name swap has to be done here
        # Otherwise, the manifest isn't aware of the file and can't work properly
        path = Path(name)
        if path.suffix == ".scss":
            # Compile scss files automatically in debug mode
            if settings.DEBUG:
                Scss.compile(
                    [
                        Scss.CompileArg(absolute=Path(p), relative=Path(name))
                        for p in find(name, all=True)
                    ]
                )
            name = str(path.with_suffix(".css"))

        elif path.suffix == ".ts":
            name = str(path.with_suffix(".js"))

        return super().url(name, force=force)

    def post_process(
        self, paths: dict[str, tuple[Storage, str]], *, dry_run: bool = False
    ):
        # Whether we get the files that were processed by ManifestFilesMixin
        # by calling super() or whether we get them from the manifest file
        # makes no difference - we have to open the manifest file anyway
        # because we need to update the paths stored inside it.
        yield from super().post_process(paths, dry_run)
        if not dry_run:
            JS.minify()
