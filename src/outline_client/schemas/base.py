from pydantic import BaseModel, ConfigDict

# =============================================================================
# CLASS: OutlineBaseModel
# =============================================================================


class OutlineBaseModel(BaseModel):
    """
    Base model shared by every schema in this package.

    The Outline API speaks `camelCase` while this package exposes `snake_case`,
    so models are populated by alias and by field name alike: responses arrive
    in the wire spelling and hand-built requests read naturally in Python.

    `extra="allow"` keeps the client forward compatible. Outline ships new
    response fields regularly and the generated models are only ever as current
    as the spec they were generated from; ignoring unknown keys would silently
    drop data that a caller can still reach through the model's `__pydantic_extra__`.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",
    )
