from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles.finders import find
from django.contrib.staticfiles.storage import (
    ManifestStaticFilesStorage,
)
from django.core.files.storage import Storage

from staticfiles.processors import JS, JSBundler, Scss


class ManifestPostProcessingStorage(ManifestStaticFilesStorage):
    def url(self, name: str, *, force: bool = False) -> str:
        """Get the URL for a file, convert .scss calls to .css calls to bundled files to their output ones"""
        # This name swap has to be done here
        # Otherwise, the manifest isn't aware of the file and can't work properly
        if settings.DEBUG:
            try:
                manifest = JSBundler.get_manifest()
            except Exception as e:
                raise Exception(
                    "Error loading manifest file, the bundler seems to be busy"
                ) from e
            converted = manifest.mapping.get(name, None)
            if converted:
                name = converted

        path = Path(name)
        # Call bundler manifest
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

        return super().url(name, force=force)

    def hashed_name(self, name, content=None, filename=None):
        # Ignore bundled files since they will be added at post process
        if JSBundler.is_in_bundle(name):
            return name
        return super().hashed_name(name, content, filename)

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

        manifest = JSBundler.get_manifest()
        self.hashed_files.update(manifest.mapping)
        self.save_manifest()
