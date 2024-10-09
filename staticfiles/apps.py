from pathlib import Path

from django.contrib.staticfiles.apps import StaticFilesConfig

GENERATED_ROOT = Path(__file__).parent.resolve() / "generated"
IGNORE_PATTERNS_WEBPACK = ["webpack/*"]
IGNORE_PATTERNS_SCSS = ["*.scss"]
IGNORE_PATTERNS_TYPESCRIPT = ["*.ts"]
IGNORE_PATTERNS = [
    *StaticFilesConfig.ignore_patterns,
    *IGNORE_PATTERNS_TYPESCRIPT,
    *IGNORE_PATTERNS_WEBPACK,
    *IGNORE_PATTERNS_SCSS,
]


# We override the original staticfiles app according to https://docs.djangoproject.com/en/4.2/ref/contrib/staticfiles/#customizing-the-ignored-pattern-list
# However, this is buggy and requires us to have an exact naming of the class like this to be detected
# Also, it requires to create all commands in management/commands again or they don't get detected by django
# Workaround originates from https://stackoverflow.com/a/78724835/12640533
class StaticFilesConfig(StaticFilesConfig):
    """
    Application in charge of processing statics files.
    It replaces the original django staticfiles
    It integrates scss files and webpack.
    It makes sure that statics are properly collected and that they are automatically
        when using the development server.
    """

    ignore_patterns = IGNORE_PATTERNS
    name = "staticfiles"
