"""
Backward-compatible re-export shim.

The canonical implementations now live in src/utils/helpers.py.
All existing imports of the form:
    from src.pipeline.utils import project_root, setup_logger, ensure_dir
continue to work without changes.
"""

from src.utils.helpers import project_root, setup_logger, ensure_dir  # noqa: F401

__all__ = ["project_root", "setup_logger", "ensure_dir"]
