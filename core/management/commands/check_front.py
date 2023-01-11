import re
from subprocess import PIPE, Popen, TimeoutExpired

from django.conf import settings
from django.core.management.base import BaseCommand

# see https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
# added "v?"
# Please note that this does not match the version of the three.js library.
# Hence, you shall have to check this one by yourself
semver_regex = re.compile(
    r"^v?"
    r"(?P<major>\d+)"
    r"\.(?P<minor>\d+)"
    r"\.(?P<patch>\d+)"
    r"(?:-(?P<prerelease>(?:\d+|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:\d+|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)


class Command(BaseCommand):
    help = "Checks the front dependencies are up to date."

    def handle(self, *args, **options):
        deps = settings.SITH_FRONT_DEP_VERSIONS

        processes = dict(
            (url, create_process(url))
            for url in deps.keys()
            if parse_semver(deps[url]) is not None
        )

        for url, process in processes.items():
            try:
                stdout, stderr = process.communicate(timeout=15)
            except TimeoutExpired:
                process.kill()
                self.stderr.write(self.style.WARNING("{}: timeout".format(url)))
                continue
                # error, notice, warning

            stdout = stdout.decode("utf-8")
            stderr = stderr.decode("utf-8")

            if stderr != "":
                self.stderr.write(self.style.WARNING(stderr.strip()))
                continue

            # get all tags, parse them as semvers and find the biggest
            tags = list_tags(stdout)
            tags = map(parse_semver, tags)
            tags = filter(lambda tag: tag is not None, tags)
            latest_version = max(tags)

            # cannot fail as those which fail are filtered in the processes dict creation
            current_version = parse_semver(deps[url])
            assert current_version is not None

            if latest_version == current_version:
                msg = "{}: {}".format(url, semver_to_s(current_version))
                self.stdout.write(self.style.SUCCESS(msg))
            else:
                msg = "{}: {} < {}".format(
                    url, semver_to_s(current_version), semver_to_s(latest_version)
                )
                self.stdout.write(self.style.ERROR(msg))


def create_process(url):
    """Spawn a "git ls-remote --tags" child process."""
    return Popen(["git", "ls-remote", "--tags", url], stdout=PIPE, stderr=PIPE)


def list_tags(s):
    """Parses "git ls-remote --tags" output. Takes a string."""
    tag_prefix = "refs/tags/"

    for line in s.strip().split("\n"):
        # an example line could be:
        # "1f41e2293f9c3c1962d2d97afa666207b98a222a\trefs/tags/foo"
        parts = line.split("\t")

        # check we have a commit ID (SHA-1 hash) and a tag name
        assert len(parts) == 2
        assert len(parts[0]) == 40
        assert parts[1].startswith(tag_prefix)

        # avoid duplicates (a peeled tag will appear twice: as "name" and as "name^{}")
        if not parts[1].endswith("^{}"):
            yield parts[1][len(tag_prefix) :]


def parse_semver(s):
    """
    Turns a semver string into a 3-tuple or None if the parsing failed, it is a
    prerelease or it has build metadata.

    See https://semver.org
    """
    m = semver_regex.match(s)

    if (
        m is None
        or m.group("prerelease") is not None
        or m.group("buildmetadata") is not None
    ):
        return None

    return (int(m.group("major")), int(m.group("minor")), int(m.group("patch")))


def semver_to_s(t):
    """Expects a 3-tuple with ints and turns it into a string of type "1.2.3"."""
    return "{}.{}.{}".format(t[0], t[1], t[2])
