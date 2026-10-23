"""Locate dist artifacts and the version recorded by a build."""

import os
from pathlib import Path


def artifact_dir(target):
    override = os.environ.get('RUNTIME_DIST')
    base = Path(override) if override else Path.cwd() / 'dist'
    return base / target


def build_version(target):
    path = artifact_dir(target) / 'VERSION'
    if not path.is_file():
        return None
    version = path.read_text().strip()
    return version or None
