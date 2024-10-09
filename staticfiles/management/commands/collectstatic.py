import shutil
from pathlib import Path

from django.contrib.staticfiles.finders import get_finders
from django.contrib.staticfiles.management.commands.collectstatic import (
    Command as CollectStatic,
)

from staticfiles.apps import GENERATED_ROOT, IGNORE_PATTERNS_SCSS
from staticfiles.processors import OpenApi, Scss, Webpack


class Command(CollectStatic):
    """Integrate webpack and css compilation to collectstatic"""

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
            for path, storage in finder.list(
                set(self.ignore_patterns) - set(IGNORE_PATTERNS_SCSS)
            ):
                path = Path(path)
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
        OpenApi.compile()  # This needs to be prior to webpack
        Webpack.compile()

        collected = super().collect()

        if self.clear_generated:
            shutil.rmtree(GENERATED_ROOT, ignore_errors=True)

        return collected
