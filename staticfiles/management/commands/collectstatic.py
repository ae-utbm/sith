import shutil
from pathlib import Path

from django.contrib.staticfiles.finders import get_finders
from django.contrib.staticfiles.management.commands.collectstatic import (
    Command as CollectStatic,
)

from staticfiles.apps import GENERATED_ROOT, IGNORE_PATTERNS_SCSS
from staticfiles.processors import JSBundler, OpenApi, Scss


class Command(CollectStatic):
    """Integrate js bundling and css compilation to collectstatic"""

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--clear-generated",
            action="store_true",
            help="Delete the generated folder after collecting statics.",
        )

    def set_options(self, **options):
        super().set_options(**options)
        self.clear_generated = options["clear_generated"]

    def collect_scss(self) -> list[Scss.CompileArg]:
        files: list[Scss.CompileArg] = []
        for finder in get_finders():
            for path_str, storage in finder.list(
                set(self.ignore_patterns) - set(IGNORE_PATTERNS_SCSS)
            ):
                path = Path(path_str)
                if path.suffix != ".scss":
                    continue
                files.append(
                    Scss.CompileArg(absolute=storage.path(path), relative=path)
                )
        return files

    def collect(self):
        if self.clear:  # Clear generated folder
            shutil.rmtree(GENERATED_ROOT, ignore_errors=True)

        def to_path(location: str | tuple[str, str]) -> Path:
            if isinstance(location, tuple):
                # staticfiles can be in a (prefix, path) format
                _, location = location
            return Path(location)

        Scss.compile(self.collect_scss())
        openapi = OpenApi.compile()  # This needs to be prior to javascript bundling
        if openapi is not None:
            _ = openapi.wait()
            if openapi.returncode:
                raise RuntimeError(
                    f"Openapi generation failed with returncode {openapi.returncode}"
                )
        JSBundler.compile()

        collected = super().collect()

        if self.clear_generated:
            shutil.rmtree(GENERATED_ROOT, ignore_errors=True)

        return collected
