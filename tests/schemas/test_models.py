"""
The generated models, and the corrections applied while generating them.

These assert the places where the published specification and the server
disagree. Each one is a rewrite in `scripts/generate_schemas.py`; a test here
fails if a regeneration drops it.
"""

import pytest
from pydantic import ValidationError

from outline_client.schemas.models import (
    Attachment,
    Collection,
    Document,
    DocumentFilterCondition,
    DocumentFilterGroup,
    GroupMembership,
    GroupPermission,
    Permission,
    User,
)

# =============================================================================
# TESTS: Specification corrections
# =============================================================================


class TestPermission:
    def test_admin_is_a_permission(self) -> None:
        # The specification lists only read and read_write; Outline's own
        # CollectionPermission and DocumentPermission have three members, and
        # a collection's templateManagement comes back as admin.
        assert Permission.ADMIN == "admin"

    def test_a_collection_with_admin_template_management_validates(self) -> None:
        collection = Collection.model_validate(
            {"name": "Handbook", "templateManagement": "admin"}
        )

        assert collection.template_management == Permission.ADMIN


class TestGroupMembership:
    def test_permission_is_a_group_role_not_an_access_level(self) -> None:
        # The specification points this at Permission; the server sends
        # member or admin.
        membership = GroupMembership.model_validate({"permission": "member"})

        assert membership.permission == GroupPermission.MEMBER

    def test_rejects_an_access_level(self) -> None:
        with pytest.raises(ValidationError):
            GroupMembership.model_validate({"permission": "read_write"})


class TestWidenedTypes:
    def test_an_attachment_url_may_be_a_path(self) -> None:
        # Outline answers with `/api/attachments.redirect?id=...`, which a
        # URL type would reject outright.
        attachment = Attachment.model_validate(
            {"url": "/api/attachments.redirect?id=abc"}
        )

        assert attachment.url == "/api/attachments.redirect?id=abc"

    def test_an_email_is_not_re_validated(self) -> None:
        # The server already accepted the address; re-validating it here would
        # only add a dependency and a way to reject real data.
        assert User.model_validate({"email": "ada@example"}).email == "ada@example"


# =============================================================================
# TESTS: Model behaviour
# =============================================================================


class TestNaming:
    def test_reads_the_wire_spelling(self) -> None:
        document = Document.model_validate(
            {"collectionId": "9884b98e-3c7b-4a8a-964d-c64ce9002d21", "fullWidth": True}
        )

        assert document.collection_id is not None
        assert document.full_width is True

    def test_also_accepts_the_python_spelling(self) -> None:
        document = Document(title="Onboarding", full_width=True)

        assert document.model_dump(by_alias=True, exclude_none=True) == {
            "title": "Onboarding",
            "fullWidth": True,
        }

    def test_keeps_fields_it_does_not_know(self) -> None:
        document = Document.model_validate({"title": "Onboarding", "newField": 1})

        assert document.__pydantic_extra__ == {"newField": 1}


class TestFilters:
    def test_a_group_nests_conditions_and_further_groups(self) -> None:
        group = DocumentFilterGroup(
            operator="OR",
            filters=[
                DocumentFilterCondition(field="title", operator="contains", value="x"),
                DocumentFilterGroup(
                    operator="AND",
                    filters=[
                        DocumentFilterCondition(
                            field="userId", operator="eq", value="u"
                        )
                    ],
                ),
            ],
        )

        assert group.model_dump(by_alias=True) == {
            "operator": "OR",
            "filters": [
                {"field": "title", "operator": "contains", "value": "x"},
                {
                    "operator": "AND",
                    "filters": [{"field": "userId", "operator": "eq", "value": "u"}],
                },
            ],
        }
