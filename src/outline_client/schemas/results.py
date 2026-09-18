"""
Result models for the composite `data` shapes the API returns.

Most Outline methods answer with a `data` that is a schema from the
specification's `components` section, which `models.py` already covers. A
minority answer with an anonymous object that bundles several of those schemas
together - `{"users": [...], "memberships": [...]}` and the like. Those objects
have no name in the specification and so no generated model; they are written
out here instead, one per distinct shape.

Every list field defaults to empty rather than `None`: Outline omits a bundle
member when it has nothing to report, and a caller iterating the result should
not have to tell "absent" from "empty".
"""

from typing import Annotated, Any

from pydantic import AliasChoices, Field

from outline_client.schemas.base import OutlineBaseModel
from outline_client.schemas.models import (
    Attachment,
    Collection,
    CollectionGroupMembership,
    Document,
    FileOperation,
    Group,
    GroupMembership,
    Invite,
    Membership,
    SearchResult,
    Star,
    User,
)

# =============================================================================
# CLASS: AuthService
# =============================================================================


class AuthService(OutlineBaseModel):
    """
    One sign-in method offered by a workspace.
    """

    id: str | None = None
    """
    Identifier for the authentication provider, e.g. `google` or `oidc`.
    """
    name: str | None = None
    """
    Human-readable name of the authentication provider.
    """
    auth_url: Annotated[str | None, Field(alias="authUrl")] = None
    """
    URL a browser is sent to in order to begin sign-in with this provider.
    """


# =============================================================================
# CLASS: AuthConfig
# =============================================================================


class AuthConfig(OutlineBaseModel):
    """
    The sign-in configuration of the workspace behind the current hostname.

    The specification calls the provider list `services`; Outline 1.10 sends it
    as `providers`, and adds the branding fields below that the specification
    does not mention. Both spellings are accepted.
    """

    name: str | None = None
    """
    Name of the workspace.
    """
    hostname: str | None = None
    """
    Hostname the configuration was resolved for. Only sent when the workspace
    is reached through its own custom domain.
    """
    logo: str | None = None
    """
    The workspace's logo, if it has opted into public branding.
    """
    custom_theme: Annotated[bool | None, Field(alias="customTheme")] = None
    """
    Whether the workspace has a custom theme applied to its sign-in page.
    """
    providers: Annotated[
        list[AuthService],
        Field(validation_alias=AliasChoices("providers", "services")),
    ] = Field(default_factory=list)
    """
    The authentication providers enabled for the workspace.
    """


# =============================================================================
# CLASS: AttachmentUpload
# =============================================================================


class AttachmentUpload(OutlineBaseModel):
    """
    A pre-authorized upload slot, returned when an attachment record is created.

    Creating an attachment only reserves it; the bytes are uploaded separately
    by the caller. `mode` says how: `post` means a multipart form POST to
    `upload_url` with `form` as the accompanying fields, and `put` means a plain
    PUT of the body to `upload_url` with `headers` applied. Either way the file
    is readable at `url` once the upload completes.
    """

    max_upload_size: Annotated[float | None, Field(alias="maxUploadSize")] = None
    """
    The largest upload the server will accept, in bytes.
    """
    mode: str | None = None
    """
    How the bytes must be uploaded, either `post` or `put`.
    """
    upload_url: Annotated[str | None, Field(alias="uploadUrl")] = None
    """
    The URL to upload the file content to.
    """
    form: dict[str, Any] = Field(default_factory=dict)
    """
    Form fields that must accompany the upload when `mode` is `post`.
    """
    headers: dict[str, Any] = Field(default_factory=dict)
    """
    Headers that must accompany the upload when `mode` is `put`.
    """
    url: str | None = None
    """
    The URL the attachment will be readable at once uploaded.
    """
    attachment: Attachment | None = None
    """
    The attachment record that was created.
    """


# =============================================================================
# CLASS: FileOperationResult
# =============================================================================


class FileOperationResult(OutlineBaseModel):
    """
    The background job started by an export or import request.

    The work is not done when the call returns. Poll
    `get_file_operation(result.file_operation.id)` until its `state` reaches
    `complete`, then download the product with `download_file_operation`.
    """

    file_operation: Annotated[FileOperation | None, Field(alias="fileOperation")] = None
    """
    The queued file operation.
    """


# =============================================================================
# CLASS: MembershipsResult
# =============================================================================


class MembershipsResult(OutlineBaseModel):
    """
    User memberships on a collection or document, with the users themselves.

    `memberships` carries the permission each user holds; `users` carries the
    matching user records, joined on `Membership.user_id`.
    """

    users: list[User] = Field(default_factory=list)
    """
    The users referenced by the memberships.
    """
    memberships: list[Membership] = Field(default_factory=list)
    """
    The memberships themselves.
    """


# =============================================================================
# CLASS: CollectionGroupMembershipsResult
# =============================================================================


class CollectionGroupMembershipsResult(OutlineBaseModel):
    """
    Group memberships on a collection, with the groups themselves.

    `groups` is only returned when listing; adding a group answers with the
    memberships alone.
    """

    groups: list[Group] = Field(default_factory=list)
    """
    The groups referenced by the memberships.
    """
    collection_group_memberships: Annotated[
        list[CollectionGroupMembership], Field(alias="collectionGroupMemberships")
    ] = Field(default_factory=list)
    """
    The memberships themselves.
    """


# =============================================================================
# CLASS: DocumentGroupMembershipsResult
# =============================================================================


class DocumentGroupMembershipsResult(OutlineBaseModel):
    """
    Group memberships on a document, with the groups themselves.

    The membership records share the `CollectionGroupMembership` shape, but
    Outline returns them under `groupMemberships` here rather than
    `collectionGroupMemberships`, which is why this is a separate model.
    """

    groups: list[Group] = Field(default_factory=list)
    """
    The groups referenced by the memberships.
    """
    group_memberships: Annotated[
        list[CollectionGroupMembership], Field(alias="groupMemberships")
    ] = Field(default_factory=list)
    """
    The memberships themselves.
    """


# =============================================================================
# CLASS: GroupMembershipsResult
# =============================================================================


class GroupMembershipsResult(OutlineBaseModel):
    """
    A bundle of group memberships with whichever related records apply.

    Which members are populated depends on the method: listing groups returns
    `groups`, listing a group's members returns `users`, and listing a user's
    memberships returns `documents` alongside them. The rest stay empty.
    """

    users: list[User] = Field(default_factory=list)
    """
    The users referenced by the memberships.
    """
    groups: list[Group] = Field(default_factory=list)
    """
    The groups referenced by the memberships.
    """
    documents: list[Document] = Field(default_factory=list)
    """
    The documents referenced by the memberships.
    """
    group_memberships: Annotated[
        list[GroupMembership], Field(alias="groupMemberships")
    ] = Field(default_factory=list)
    """
    The memberships themselves.
    """


# =============================================================================
# CLASS: DocumentsResult
# =============================================================================


class DocumentsResult(OutlineBaseModel):
    """
    A set of documents affected by one call, such as a recursive duplicate.
    """

    documents: list[Document] = Field(default_factory=list)
    """
    The affected documents.
    """


# =============================================================================
# CLASS: DocumentMoveResult
# =============================================================================


class DocumentMoveResult(OutlineBaseModel):
    """
    The documents and collections whose position changed during a move.

    A move rewrites the document structure of both the source and the
    destination collection, so both are returned in their new state.
    """

    documents: list[Document] = Field(default_factory=list)
    """
    The moved document and any children that moved with it.
    """
    collections: list[Collection] = Field(default_factory=list)
    """
    The collections whose document structure changed.
    """


# =============================================================================
# CLASS: CollectionIndex
# =============================================================================


class CollectionIndex(OutlineBaseModel):
    """
    The fractional index a collection was moved to.

    Outline orders collections by an opaque, sortable string rather than by a
    number, so that inserting between two neighbours never renumbers the rest.
    """

    index: str | None = None
    """
    The collection's new sort index.
    """


# =============================================================================
# CLASS: StarsResult
# =============================================================================


class StarsResult(OutlineBaseModel):
    """
    The caller's stars, with the documents they point at.
    """

    stars: list[Star] = Field(default_factory=list)
    """
    The stars themselves.
    """
    documents: list[Document] = Field(default_factory=list)
    """
    The starred documents.
    """


# =============================================================================
# CLASS: UserMembershipsResult
# =============================================================================


class UserMembershipsResult(OutlineBaseModel):
    """
    The documents shared directly with the caller, with the memberships.
    """

    memberships: list[Membership] = Field(default_factory=list)
    """
    The memberships themselves.
    """
    documents: list[Document] = Field(default_factory=list)
    """
    The documents referenced by the memberships.
    """


# =============================================================================
# CLASS: InvitesResult
# =============================================================================


class InvitesResult(OutlineBaseModel):
    """
    The outcome of an invitation request.

    `sent` lists the invitations that were newly created; an address that
    already belongs to a workspace member is skipped rather than rejected, so
    `sent` can be shorter than the list that was submitted.
    """

    sent: list[Invite] = Field(default_factory=list)
    """
    The invitations that were sent.
    """
    users: list[User] = Field(default_factory=list)
    """
    The user records created for the invited addresses.
    """


# =============================================================================
# CLASS: SearchHit
# =============================================================================


class SearchHit(OutlineBaseModel):
    """
    One document matched by a full-text search, with its matching context.
    """

    context: str | None = None
    """
    A snippet of the document surrounding the match, with the query terms
    wrapped in markdown bold markers.
    """
    ranking: float | None = None
    """
    Relevance score of this hit; higher ranks closer to the query.
    """
    document: Document | None = None
    """
    The matched document.
    """


# =============================================================================
# CLASS: AnswerResult
# =============================================================================


class AnswerResult(OutlineBaseModel):
    """
    A natural-language answer to a question, with the documents it drew on.

    This is the one method whose payload is not wrapped in `data`; the fields
    below are the whole response body.
    """

    documents: list[Document] = Field(default_factory=list)
    """
    The documents the answer was drawn from.
    """
    search: SearchResult | None = None
    """
    The recorded query and the answer generated for it.
    """
