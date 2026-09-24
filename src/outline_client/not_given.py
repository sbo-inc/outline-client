"""
The default for an argument whose `None` means something.

A client method leaves an argument at `None` out of the request. For the few
fields Outline accepts as JSON null, null and omission mean different things:
null clears the field, and omission leaves it alone. Those arguments default to
`NOT_GIVEN` instead, so `None` is free to mean null. The pattern is the one
openai-python and anthropic-sdk-python use.

    outline.update_document(document_id, icon=None)  # clears the icon
    outline.update_document(document_id, title="Renamed")  # leaves it alone
"""

from typing import Literal, final, override

# =============================================================================
# CLASS: NotGiven
# =============================================================================


@final
class NotGiven:
    """
    The type of `NOT_GIVEN`, the default of an argument Outline accepts as null.

    Falsy, so `if icon:` reads an omitted argument as it reads an empty one,
    and shown as `NOT_GIVEN`, so a debug print says what the argument is
    rather than where it lives in memory.
    """

    def __bool__(self) -> Literal[False]:
        return False

    @override
    def __repr__(self) -> str:
        return "NOT_GIVEN"


NOT_GIVEN = NotGiven()
"""
The default of an argument Outline accepts as null: the field is not sent.
"""
