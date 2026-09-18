"""
Regenerate `outline_client.schemas.models` from the Outline OpenAPI spec.

Run through `make schemas`. The work is three steps: invoke
datamodel-code-generator over the published specification, rewrite the handful
of things it cannot get right on its own, and hand the result to ruff.

Two rewrites are applied, both explained where they are defined below: the
format-derived types are widened back to `str`, and the names
datamodel-code-generator invents for anonymous sub-schemas are replaced with
ones that say what they are. Both rename maps are asserted against the
generated source, so a specification change that invalidates one fails the
regeneration loudly instead of quietly skipping it.
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "src" / "outline_client" / "schemas" / "models.py"
HEADER = ROOT / ".codegen-header.txt"

SPEC_URL = "https://raw.githubusercontent.com/outline/openapi/main/spec3.json"

BASE_CLASS = "outline_client.schemas.base.OutlineBaseModel"

# -----------------------------------------------------------------------------
# Widened types
# -----------------------------------------------------------------------------
#
# The specification annotates several string fields with `format: uri` or
# `format: email`, which datamodel-code-generator turns into `AnyUrl` and
# `EmailStr`. Both are wrong for a client.
#
# `AnyUrl` rejects the relative paths Outline actually returns - an attachment's
# `url` is `/api/attachments.redirect?id=...` - and parses the absolute ones
# into a `Url` object that no longer compares equal to the string it came from.
# `EmailStr` pulls in the optional `email-validator` dependency to re-validate
# an address the server already accepted.
#
# A client's job is to hand back what the server sent, so both widen to `str`.

WIDENED_TYPES = {
    "AnyUrl": "str",
    "EmailStr": "str",
}

# -----------------------------------------------------------------------------
# Renamed classes
# -----------------------------------------------------------------------------
#
# Anonymous sub-schemas - an inline enum, or one branch of a `oneOf` - have no
# name in the specification, so datamodel-code-generator invents one from the
# property it was found under and disambiguates collisions with a counter. That
# yields `Operator1` and `Field3`, which say nothing about what they belong to
# and shift whenever the specification grows another inline enum.
#
# Each is renamed here to the name it would have been given had the
# specification named it. The four `Operator*` enums that are all `AND`/`OR`
# collapse to nothing - the filter-group models reference them by these names -
# so they are numbered in the order they appear rather than merged, which would
# require editing the models that use them.

RENAMED_CLASSES = {
    # AccessRequest.status
    "Status": "AccessRequestStatus",
    # Sorting.direction / Collection.sort.direction
    "Direction": "SortDirection",
    "Direction1": "CollectionSortDirection",
    "Sort": "CollectionSort",
    # Collection / Revision `sourceMetadata`
    "SourceMetadata": "CollectionSourceMetadata",
    "SourceMetadata1": "RevisionSourceMetadata",
    "AuthType": "EventAuthType",
    "AuthType1": "RevisionAuthType",
    # DocumentFilter oneOf branches and their inline enums
    "FieldModel": "DocumentFilterField",
    "Operator": "DocumentFilterOperator",
    "DocumentFilter1": "DocumentFilterCondition",
    "DocumentFilter2": "DocumentFilterGroup",
    "Operator1": "DocumentFilterGroupOperator",
    # DocumentsDeletedFilter oneOf branches
    "Field1": "DocumentsDeletedFilterField",
    "Operator2": "DocumentsDeletedFilterOperator",
    "DocumentsDeletedFilter1": "DocumentsDeletedFilterCondition",
    "DocumentsDeletedFilter2": "DocumentsDeletedFilterGroup",
    "Operator3": "DocumentsDeletedFilterGroupOperator",
    # CollectionFilter oneOf branches
    "Field2": "CollectionFilterField",
    "Operator4": "CollectionFilterOperator",
    "CollectionFilter1": "CollectionFilterCondition",
    "CollectionFilter2": "CollectionFilterGroup",
    "Operator5": "CollectionFilterGroupOperator",
    # UserFilter oneOf branches
    "Field3": "UserFilterField",
    "Operator6": "UserFilterOperator",
    "UserFilter1": "UserFilterCondition",
    "UserFilter2": "UserFilterGroup",
    "Operator7": "UserFilterGroupOperator",
    # FileOperation.type / .state
    "Type": "FileOperationType",
    "State": "FileOperationState",
    # DataAttributeOptions.options[]
    "Option": "DataAttributeOption",
    # Document.tasks / .preferences
    "Tasks": "DocumentTasks",
    "HeadingPrefix": "DocumentHeadingPrefix",
    "Preferences": "DocumentPreferences",
    # DocumentInsight.period
    "Period": "DocumentInsightPeriod",
    # OAuthClient.type, and the reduced client nested in OAuthAuthentication
    "ClientType": "OAuthClientType",
    "OauthClient": "OAuthClientSummary",
    # SearchResult.source
    "Source": "SearchResultSource",
}


# -----------------------------------------------------------------------------
# Specification corrections
# -----------------------------------------------------------------------------
#
# Places where the published specification disagrees with what the server
# actually sends, verified against a running Outline 1.10. A client that
# believes the specification here rejects valid responses, so the models are
# corrected to match the server.
#
# Each correction is an exact `(find, replace)` pair applied to the generated
# source; a pair whose `find` no longer matches fails the regeneration, which
# is how a specification fix gets noticed.

PATCHES: list[tuple[str, str]] = [
    # `Permission` is missing `admin`. Outline's own `CollectionPermission`
    # and `DocumentPermission` enums have three members, and a collection's
    # `templateManagement` comes back as `admin` on a default installation.
    (
        'class Permission(StrEnum):\n    READ = "read"\n    READ_WRITE = "read_write"\n',
        'class Permission(StrEnum):\n    READ = "read"\n    READ_WRITE = "read_write"\n    ADMIN = "admin"\n',
    ),
    # A group membership's `permission` is a role within the group, not an
    # access level: the server sends `member` or `admin`, which is Outline's
    # `GroupPermission` rather than the `Permission` the specification points
    # at. The enum has no name in the specification, so it is defined here.
    (
        "class GroupMembership(OutlineBaseModel):",
        "class GroupPermission(StrEnum):\n"
        '    """\n'
        "    A member's role within a group.\n"
        '    """\n'
        "\n"
        '    MEMBER = "member"\n'
        '    ADMIN = "admin"\n'
        "\n"
        "\n"
        "class GroupMembership(OutlineBaseModel):",
    ),
    (
        "    permission: Permission | None = None\n"
        '    source_id: Annotated[UUID | None, Field(alias="sourceId")] = None\n'
        '    """\n'
        "    Identifier for the membership this one was inherited from, if any.\n"
        '    """\n'
        "\n"
        "\n"
        "class CollectionGroupMembership(OutlineBaseModel):",
        "    permission: GroupPermission | None = None\n"
        '    source_id: Annotated[UUID | None, Field(alias="sourceId")] = None\n'
        '    """\n'
        "    Identifier for the membership this one was inherited from, if any.\n"
        '    """\n'
        "\n"
        "\n"
        "class CollectionGroupMembership(OutlineBaseModel):",
    ),
]


# =============================================================================
# FUNCTION: generate
# =============================================================================


def generate() -> str:
    """
    Run datamodel-code-generator over the published specification.

    Returns:
        str: The generated module source.
    """
    subprocess.run(
        [
            "datamodel-codegen",
            "--url",
            SPEC_URL,
            "--input-file-type",
            "openapi",
            # Only `components/schemas`. Request and response bodies are
            # defined inline per path, so generating them too would produce a
            # model per operation named after its path; the client builds those
            # payloads from typed arguments instead.
            "--openapi-scopes",
            "schemas",
            "--output",
            str(OUTPUT),
            "--output-model-type",
            "pydantic_v2.BaseModel",
            "--target-python-version",
            "3.12",
            "--base-class",
            BASE_CLASS,
            "--snake-case-field",
            "--use-standard-collections",
            "--use-union-operator",
            "--use-annotated",
            "--field-constraints",
            "--use-schema-description",
            "--use-field-description",
            "--use-default-kwarg",
            # Unwrap the single-member `RootModel`s the `oneOf` filters would
            # otherwise become, so a filter is built as the branch itself
            # rather than through a wrapper.
            "--collapse-root-models",
            "--capitalise-enum-members",
            "--disable-timestamp",
            "--formatters",
            "ruff-format",
            "--custom-file-header-path",
            str(HEADER),
        ],
        check=True,
        cwd=ROOT,
    )

    return OUTPUT.read_text()


# =============================================================================
# FUNCTION: drop_imports
# =============================================================================


def drop_imports(source: str, names: dict[str, str]) -> str:
    """
    Remove the widened names from the `pydantic` import.

    The widening turns `AnyUrl` into `str` everywhere it appears, and the import
    line is no such exception - rewriting it would leave `from pydantic import
    str`. The names are dropped from the import first so the rename only ever
    sees real annotations.

    Returns:
        str: The source with the widened names no longer imported.
    """

    def rewrite(match: re.Match[str]) -> str:
        kept = [
            name
            for name in (part.strip() for part in match.group(1).split(","))
            if name and name not in names
        ]
        return f"from pydantic import {', '.join(kept)}\n" if kept else ""

    return re.sub(r"from pydantic import ([^\n]+)\n", rewrite, source, count=1)


# =============================================================================
# FUNCTION: rename
# =============================================================================


def rename(source: str, replacements: dict[str, str], label: str) -> str:
    """
    Replace whole-word identifiers in the generated source.

    Every key must appear, so a specification change that removes one is
    reported rather than silently leaving the module half-renamed.

    Returns:
        str: The source with the replacements applied.
    """
    missing = [old for old in replacements if not re.search(rf"\b{old}\b", source)]
    if missing:
        raise SystemExit(
            f"{label}: no longer present in the generated models: {', '.join(missing)}.\n"
            "The specification has changed; update scripts/generate_schemas.py."
        )

    pattern = re.compile(r"\b(" + "|".join(map(re.escape, replacements)) + r")\b")

    return pattern.sub(lambda match: replacements[match.group()], source)


# =============================================================================
# FUNCTION: patch
# =============================================================================


def patch(source: str, patches: list[tuple[str, str]]) -> str:
    """
    Apply the exact-match corrections, failing on any that no longer matches.

    Returns:
        str: The corrected source.
    """
    for index, (find, replace) in enumerate(patches):
        if find not in source:
            raise SystemExit(
                f"correction {index} no longer matches the generated models.\n"
                "The specification has changed; update scripts/generate_schemas.py."
            )
        source = source.replace(find, replace, 1)

    return source


# =============================================================================
# FUNCTION: main
# =============================================================================


def main() -> int:
    """
    Generate, rewrite, and format the schema module.

    Returns:
        int: The process exit code.
    """
    source = generate()
    source = drop_imports(source, WIDENED_TYPES)
    source = rename(source, WIDENED_TYPES, "widened types")
    source = rename(source, RENAMED_CLASSES, "renamed classes")
    source = patch(source, PATCHES)
    OUTPUT.write_text(source)

    # The rewrites leave the `AnyUrl`/`EmailStr` import unused and the renames
    # leave the classes out of definition order for ruff's import sorting.
    subprocess.run(
        ["ruff", "check", "--fix", "--unsafe-fixes", "--quiet", str(OUTPUT)],
        check=False,
        cwd=ROOT,
    )
    subprocess.run(["ruff", "format", "--quiet", str(OUTPUT)], check=True, cwd=ROOT)

    return 0


if __name__ == "__main__":
    sys.exit(main())
