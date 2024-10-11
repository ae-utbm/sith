import logging
import subprocess
from dataclasses import dataclass
from hashlib import sha1
from pathlib import Path
from typing import Iterable

import rjsmin
import sass
from django.conf import settings

from sith.urls import api
from staticfiles.apps import GENERATED_ROOT


class Webpack:
    @staticmethod
    def compile():
        """Bundle js files with webpack for production."""
        process = subprocess.Popen(["npm", "run", "compile"])
        process.wait()
        if process.returncode:
            raise RuntimeError(f"Webpack failed with returncode {process.returncode}")

    @staticmethod
    def runserver() -> subprocess.Popen:
        """Bundle js files automatically in background when called in debug mode."""
        logging.getLogger("django").info("Running webpack server")
        return subprocess.Popen(["npm", "run", "serve"])


class Scss:
    @dataclass
    class CompileArg:
        absolute: Path  # Absolute path to the file
        relative: Path  # Relative path inside the folder it has been collected

    @staticmethod
    def compile(files: CompileArg | Iterable[CompileArg]):
        """Compile scss files to css files."""
        # Generate files inside the generated folder
        # .css files respects the hierarchy in the static folder it was found
        # This converts arg.absolute -> generated/{arg.relative}.scss
        # Example:
        #   app/static/foo.scss          -> generated/foo.css
        #   app/static/bar/foo.scss      -> generated/bar/foo.css
        #   custom/location/bar/foo.scss -> generated/bar/foo.css
        if isinstance(files, Scss.CompileArg):
            files = [files]

        base_args = {"output_style": "compressed", "precision": settings.SASS_PRECISION}

        compiled_files = {
            file.relative.with_suffix(".css"): sass.compile(
                filename=str(file.absolute), **base_args
            )
            for file in files
        }
        for file, content in compiled_files.items():
            dest = GENERATED_ROOT / file
            dest.parent.mkdir(exist_ok=True, parents=True)
            dest.write_text(content)


class JS:
    @staticmethod
    def minify():
        to_exec = [
            p for p in settings.STATIC_ROOT.rglob("*.js") if ".min" not in p.suffixes
        ]
        for path in to_exec:
            p = path.resolve()
            minified = rjsmin.jsmin(p.read_text())
            p.write_text(minified)
            logging.getLogger("main").info(f"Minified {path}")


class OpenApi:
    OPENAPI_DIR = GENERATED_ROOT / "openapi"

    @classmethod
    def compile(cls):
        """Compile a typescript client for the sith API. Only generates it if it changed"""
        logging.getLogger("django").info("Compiling open api typescript client")
        out = cls.OPENAPI_DIR / "schema.json"
        cls.OPENAPI_DIR.mkdir(parents=True, exist_ok=True)

        old_hash = ""
        if out.exists():
            with open(out, "rb") as f:
                old_hash = sha1(f.read()).hexdigest()

        schema = api.get_openapi_schema()
        # Remove hash from operationIds
        # This is done for cache invalidation but this is too aggressive
        for path in schema["paths"].values():
            for action, desc in path.items():
                path[action]["operationId"] = "_".join(
                    desc["operationId"].split("_")[:-1]
                )
        schema = str(schema)

        if old_hash == sha1(schema.encode("utf-8")).hexdigest():
            logging.getLogger("django").info("✨ Api did not change, nothing to do ✨")
            return

        with open(out, "w") as f:
            _ = f.write(schema)

        subprocess.run(["npx", "openapi-ts"]).check_returncode()
