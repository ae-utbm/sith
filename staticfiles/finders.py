import os

from django.contrib.staticfiles import utils
from django.contrib.staticfiles.finders import FileSystemFinder
from django.core.files.storage import FileSystemStorage

from staticfiles.apps import GENERATED_ROOT, IGNORE_PATTERNS_WEBPACK


class GeneratedFilesFinder(FileSystemFinder):
    """Find generated and regular static files"""

    def __init__(self, app_names=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add GENERATED_ROOT after adding everything in settings.STATICFILES_DIRS
        self.locations.append(("", GENERATED_ROOT))
        generated_storage = FileSystemStorage(location=GENERATED_ROOT)
        generated_storage.prefix = ""
        self.storages[GENERATED_ROOT] = generated_storage

    def list(self, ignore_patterns: list[str]):
        # List all files availables
        for _, root in self.locations:
            # Skip nonexistent directories.
            if not os.path.isdir(root):
                continue

            ignored = ignore_patterns
            # We don't want to ignore webpack files in the generated folder
            if root == GENERATED_ROOT:
                ignored = list(set(ignored) - set(IGNORE_PATTERNS_WEBPACK))

            storage = self.storages[root]
            for path in utils.get_files(storage, ignored):
                yield path, storage
