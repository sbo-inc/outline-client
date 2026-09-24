"""
Enums the specification leaves out, written by hand until it carries them.

`models.py` is generated from the specification's `components` section, so an
enum that Outline's server accepts but the specification never names has no
generated counterpart. Each one here is copied from Outline's own source, and
moves to `models.py` once the specification catches up.
"""

from enum import StrEnum

# =============================================================================
# CLASS: CommentStatusFilter
# =============================================================================


class CommentStatusFilter(StrEnum):
    """
    Which comment threads `comments.list` returns, by resolution status.

    Mirrors Outline's `CommentStatusFilter`. Passing both values, or neither,
    returns every comment.
    """

    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
