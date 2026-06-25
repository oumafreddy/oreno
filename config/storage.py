import logging
from django.contrib.staticfiles.storage import ManifestStaticFilesStorage

logger = logging.getLogger(__name__)


class ForgivingManifestStaticFilesStorage(ManifestStaticFilesStorage):
    """ManifestStaticFilesStorage that:
    1. Falls back to plain URL when a file is not in the manifest (manifest_strict=False)
    2. Skips unreferenced source map (.map) files during post-processing instead of crashing
    """
    manifest_strict = False

    def hashed_name(self, name, content=None, filename=None):
        try:
            return super().hashed_name(name, content=content, filename=filename)
        except ValueError:
            # File not found (e.g. missing .map file referenced in minified JS) — return plain name
            logger.debug("Static file not found during hashing, skipping: %s", name)
            return name
