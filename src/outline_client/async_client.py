from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import date, datetime
from typing import IO, Any, Self

import httpx

from outline_client.operations import access_requests as access_request_ops
from outline_client.operations import api_keys as api_key_ops
from outline_client.operations import attachments as attachment_ops
from outline_client.operations import auth as auth_ops
from outline_client.operations import collections as collection_ops
from outline_client.operations import comments as comment_ops
from outline_client.operations import data_attributes as data_attribute_ops
from outline_client.operations import documents as document_ops
from outline_client.operations import events as event_ops
from outline_client.operations import file_operations as file_operation_ops
from outline_client.operations import groups as group_ops
from outline_client.operations import notifications as notification_ops
from outline_client.operations import oauth as oauth_ops
from outline_client.operations import pins as pin_ops
from outline_client.operations import reactions as reaction_ops
from outline_client.operations import revisions as revision_ops
from outline_client.operations import shares as share_ops
from outline_client.operations import stars as star_ops
from outline_client.operations import subscriptions as subscription_ops
from outline_client.operations import templates as template_ops
from outline_client.operations import users as user_ops
from outline_client.operations import views as view_ops
from outline_client.operations import webhook_subscriptions as webhook_ops
from outline_client.operations.generic import Operation, body, form_fields
from outline_client.schemas.enums import CommentStatusFilter
from outline_client.schemas.models import (
    AccessRequest,
    ApiKey,
    Attachment,
    Auth,
    Collection,
    CollectionFilterCondition,
    CollectionFilterGroup,
    CollectionStatus,
    Comment,
    DataAttribute,
    DataAttributeDataType,
    DataAttributeOptions,
    Document,
    DocumentDataAttribute,
    DocumentInsight,
    DocumentPreferences,
    Event,
    FileOperation,
    FileOperationType,
    Group,
    Invite,
    Membership,
    NavigationNode,
    Notification,
    OAuthAuthentication,
    OAuthClient,
    Permission,
    Pin,
    Reaction,
    Revision,
    RevisionDetail,
    Share,
    SortDirection,
    Star,
    Subscription,
    Template,
    TextEditMode,
    User,
    UserFilterCondition,
    UserFilterGroup,
    UserRole,
    View,
    WebhookSubscription,
)
from outline_client.schemas.results import (
    AnswerResult,
    AttachmentUpload,
    AuthConfig,
    CollectionGroupMembershipsResult,
    CollectionIndex,
    DocumentGroupMembershipsResult,
    DocumentMoveResult,
    DocumentsResult,
    FileOperationResult,
    GroupMembershipsResult,
    InvitesResult,
    MembershipsResult,
    SearchHit,
    StarsResult,
    UserMembershipsResult,
)
from outline_client.transport import DEFAULT_TIMEOUT, BaseOutlineClient, logger

# =============================================================================
# CLASS: AsyncOutlineClient
# =============================================================================


class AsyncOutlineClient(BaseOutlineClient):
    """
    Asynchronous Outline API client.

    The same surface as `OutlineClient`, awaited. Both build the same
    operations and differ only in how they put them on the wire, so a method
    here takes the same arguments and returns the same models as its
    counterpart there.

    https://www.getoutline.com/developers
    """

    def __init__(
        self,
        url: str | None = None,
        token: str | None = None,
        headers: dict[str, str] = {},
        log: bool = False,
        timeout: float | tuple[float, float] | None = DEFAULT_TIMEOUT,
        retries: int | None = None,
    ) -> None:
        """
        Create a new asynchronous client for the Outline API.

        Args:
            url: The base URL of the API. A workspace URL such as
                `https://outline.example.com` is accepted and has `/api` appended.
                (Environment: `OUTLINE_API_URL`, default the cloud host)
            token: The API token to authenticate with.
                (Environment: `OUTLINE_API_TOKEN`)
            headers: Additional headers to include in requests.
            log: Enables request logging at INFO level.
            timeout: Per-request timeout in seconds applied to every call.
                Accepts a single float, a `(connect, read)` tuple, or `None`
                to disable. Defaults to `DEFAULT_TIMEOUT`.
            retries: Number of times to retry connection-establishment
                failures. A retry only ever happens before any bytes reach the
                server, so it is safe for the non-idempotent POSTs this client
                issues: a create can never be double-submitted. `None`
                (default) disables retries.
        """
        super().__init__(url=url, token=token, log=log, timeout=timeout)

        # `Content-Type` is deliberately not set here. httpx derives it per
        # request from the body it is given - `application/json` for the typed
        # methods, `multipart/form-data` with a generated boundary for
        # `import_document` - and a client-wide default would override the
        # second with a value that makes the upload unparseable.
        self._http = httpx.AsyncClient(
            headers=headers,
            transport=httpx.AsyncHTTPTransport(retries=retries) if retries else None,
        )

    @property
    def http(self) -> httpx.AsyncClient:
        return self._http

    # -------------------------------------------------------------------------
    # METHOD: aclose
    # -------------------------------------------------------------------------

    async def aclose(self) -> None:
        """
        Close the underlying HTTP client and its connection pool.
        """
        await self._http.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()

    # -------------------------------------------------------------------------
    # METHOD: request
    # -------------------------------------------------------------------------

    async def request(
        self,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        POST one API method and return the decoded body.

        The escape hatch beneath the typed methods, for the three things they
        deliberately do not offer: reading the `policies` and `pagination` a
        response carries alongside its `data`, sending a field as an explicit
        JSON `null` rather than omitting it, and calling a method this release
        does not yet cover.

        Returns:
            dict[str, Any]: The decoded JSON response body.
        """
        url = self._endpoint(path)
        logger.info("POST %s", url)

        response = await self._http.post(
            url=url,
            json=payload or {},
            headers=self._headers(),
            timeout=self._request_timeout(),
        )

        return self._decode(response)

    # -------------------------------------------------------------------------
    # METHOD: _run
    # -------------------------------------------------------------------------

    async def _run[T](self, operation: Operation[T]) -> T:
        """
        Send one operation and parse its response.

        Returns:
            T: Whatever the operation's parser produces.
        """
        return operation.parse(await self.request(operation.path, operation.payload))

    # -------------------------------------------------------------------------
    # METHOD: _download
    # -------------------------------------------------------------------------

    async def _download(self, path: str, payload: dict[str, Any], accept: str) -> bytes:
        """
        POST one API method and return the response body as bytes.

        Used by the methods whose response is a file rather than JSON. Outline
        may answer with the bytes directly or with a redirect to storage, so
        redirects are followed; httpx drops the `Authorization` header when a
        redirect crosses origins, so the token is not handed to the storage
        host.

        Returns:
            bytes: The response body.
        """
        url = self._endpoint(path)
        logger.info("POST %s", url)

        response = await self._http.post(
            url=url,
            json=payload,
            headers=self._headers(accept=accept),
            timeout=self._request_timeout(),
            follow_redirects=True,
        )
        if not response.is_success:
            self._raise_for_status(response)

        return response.content

    # -------------------------------------------------------------------------
    # METHOD: paginate
    # -------------------------------------------------------------------------

    async def paginate[T](
        self,
        method: Callable[..., Awaitable[list[T]]],
        /,
        *,
        limit: int = 100,
        **kwargs: Any,
    ) -> AsyncIterator[T]:
        """
        Walk every page of any `list_*` method, yielding the records.

        Outline's pagination reports the window it served rather than a total,
        so a page shorter than `limit` is the only signal that the end has been
        reached - which is what this stops on.

        Args:
            method: The bound `list_*` method to page through.
            limit: How many records to request per call.
            **kwargs: Forwarded to `method` on every call.

        Returns:
            AsyncIterator[T]: Every record, in the order the API returned them.
        """
        offset = 0
        while True:
            page = await method(offset=offset, limit=limit, **kwargs)
            for record in page:
                yield record

            if len(page) < limit:
                return

            offset += limit

    # =========================================================================
    # SECTION: Auth
    # =========================================================================

    # -------------------------------------------------------------------------
    # METHOD: get_auth_info
    # -------------------------------------------------------------------------

    async def get_auth_info(self) -> Auth:
        """
        Retrieve the user and workspace the API token belongs to.

        Returns:
            Auth: The authenticated user and their workspace.
        """
        return await self._run(auth_ops.get_auth_info())

    # -------------------------------------------------------------------------
    # METHOD: get_auth_config
    # -------------------------------------------------------------------------

    async def get_auth_config(self) -> AuthConfig:
        """
        Retrieve the sign-in configuration for the workspace at this hostname.

        Answered without authentication, so it is also the cheapest way to
        check that a self-hosted URL is reachable and is in fact Outline.

        Returns:
            AuthConfig: The workspace name and its authentication providers.
        """
        return await self._run(auth_ops.get_auth_config())

    # -------------------------------------------------------------------------
    # METHOD: sign_out
    # -------------------------------------------------------------------------

    async def sign_out(self) -> bool:
        """
        Sign out, invalidating the session behind the current credentials.

        Returns:
            bool: Whether the call succeeded.
        """
        return await self._run(auth_ops.sign_out())

    # =========================================================================
    # SECTION: Users
    # =========================================================================

    # -------------------------------------------------------------------------
    # METHOD: list_users
    # -------------------------------------------------------------------------

    async def list_users(
        self,
        *,
        query: str | None = None,
        filters: list[UserFilterCondition | UserFilterGroup] | None = None,
        emails: list[str] | None = None,
        filter: str | None = None,
        role: UserRole | str | None = None,
        offset: int | None = None,
        limit: int | None = None,
        sort: str | None = None,
        direction: SortDirection | str | None = None,
    ) -> list[User]:
        """
        List the users in the workspace.

        Args:
            query: Match users whose name or email contains this text.
            filters: Structured filter expression, evaluated as an AND of the
                top-level entries.
            emails: Deprecated; prefer an `email` condition in `filters`.
            filter: Deprecated; prefer `filters`.
            role: Deprecated; prefer a `role` condition in `filters`.
            offset: How many records to skip.
            limit: How many records to return.
            sort: Field to order by.
            direction: `ASC` or `DESC`.

        Returns:
            list[User]: The matching users.
        """
        return await self._run(
            user_ops.list_users(
                query=query,
                filters=filters,
                emails=emails,
                filter=filter,
                role=role,
                offset=offset,
                limit=limit,
                sort=sort,
                direction=direction,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: get_user
    # -------------------------------------------------------------------------

    async def get_user(self, id: str) -> User:
        """
        Retrieve one user.

        Returns:
            User: The user.
        """
        return await self._run(user_ops.get_user(id))

    # -------------------------------------------------------------------------
    # METHOD: invite_users
    # -------------------------------------------------------------------------

    async def invite_users(
        self,
        invites: list[Invite],
        *,
        suppress_email: bool | None = None,
    ) -> InvitesResult:
        """
        Invite people to the workspace by email address.

        Args:
            invites: The name, email, and role to invite each person under.
            suppress_email: Create the accounts without sending the emails.

        Returns:
            InvitesResult: The invitations sent and the users created for them.
        """
        return await self._run(
            user_ops.invite_users(invites, suppress_email=suppress_email)
        )

    # -------------------------------------------------------------------------
    # METHOD: resend_invite
    # -------------------------------------------------------------------------

    async def resend_invite(self, id: str) -> bool:
        """
        Send a pending invitation again.

        Returns:
            bool: Whether the call succeeded.
        """
        return await self._run(user_ops.resend_invite(id))

    # -------------------------------------------------------------------------
    # METHOD: update_user
    # -------------------------------------------------------------------------

    async def update_user(
        self,
        *,
        name: str | None = None,
        language: str | None = None,
        avatar_url: str | None = None,
        preferences: dict[str, Any] | None = None,
    ) -> User:
        """
        Update the calling user's own profile.

        This method always acts on the token's own user; changing somebody
        else's record is done through `update_user_role`, `suspend_user`, and
        `update_user_email`.

        Returns:
            User: The updated user.
        """
        return await self._run(
            user_ops.update_user(
                name=name,
                language=language,
                avatar_url=avatar_url,
                preferences=preferences,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: update_user_email
    # -------------------------------------------------------------------------

    async def update_user_email(self, email: str, *, id: str | None = None) -> bool:
        """
        Change a user's email address.

        Omitting `id` changes the calling user's own address, which Outline
        confirms by email before it takes effect. An admin passing `id`
        changes another user's address immediately.

        Returns:
            bool: Whether the call succeeded.
        """
        return await self._run(user_ops.update_user_email(email, id=id))

    # -------------------------------------------------------------------------
    # METHOD: update_user_role
    # -------------------------------------------------------------------------

    async def update_user_role(self, id: str, role: UserRole | str) -> User:
        """
        Change a user's workspace role.

        Returns:
            User: The updated user.
        """
        return await self._run(user_ops.update_user_role(id, role))

    # -------------------------------------------------------------------------
    # METHOD: suspend_user
    # -------------------------------------------------------------------------

    async def suspend_user(self, id: str) -> User:
        """
        Suspend a user, revoking their access without deleting their records.

        Returns:
            User: The suspended user.
        """
        return await self._run(user_ops.suspend_user(id))

    # -------------------------------------------------------------------------
    # METHOD: activate_user
    # -------------------------------------------------------------------------

    async def activate_user(self, id: str) -> User:
        """
        Restore a suspended user's access.

        Returns:
            User: The activated user.
        """
        return await self._run(user_ops.activate_user(id))

    # -------------------------------------------------------------------------
    # METHOD: delete_user
    # -------------------------------------------------------------------------

    async def delete_user(self, id: str) -> bool:
        """
        Delete a user and the personal data attached to them.

        Returns:
            bool: Whether the call succeeded.
        """
        return await self._run(user_ops.delete_user(id))

    # -------------------------------------------------------------------------
    # METHOD: subscribe_to_notifications
    # -------------------------------------------------------------------------

    async def subscribe_to_notifications(self, event_type: str) -> User:
        """
        Subscribe the calling user to one kind of notification.

        Returns:
            User: The updated user, with the new notification settings.
        """
        return await self._run(user_ops.subscribe_to_notifications(event_type))

    # -------------------------------------------------------------------------
    # METHOD: unsubscribe_from_notifications
    # -------------------------------------------------------------------------

    async def unsubscribe_from_notifications(self, event_type: str) -> User:
        """
        Unsubscribe the calling user from one kind of notification.

        Returns:
            User: The updated user, with the new notification settings.
        """
        return await self._run(user_ops.unsubscribe_from_notifications(event_type))

    # -------------------------------------------------------------------------
    # METHOD: list_user_memberships
    # -------------------------------------------------------------------------

    async def list_user_memberships(
        self,
        *,
        offset: int | None = None,
        limit: int | None = None,
    ) -> UserMembershipsResult:
        """
        List the documents shared directly with the calling user.

        Returns:
            UserMembershipsResult: The memberships and the documents they
                refer to.
        """
        return await self._run(
            user_ops.list_user_memberships(offset=offset, limit=limit)
        )

    # -------------------------------------------------------------------------
    # METHOD: update_user_membership
    # -------------------------------------------------------------------------

    async def update_user_membership(self, id: str, index: str) -> Membership:
        """
        Reorder one of the calling user's shared documents in the sidebar.

        Returns:
            Membership: The updated membership.
        """
        return await self._run(user_ops.update_user_membership(id, index))

    # =========================================================================
    # SECTION: Groups
    # =========================================================================

    # -------------------------------------------------------------------------
    # METHOD: list_groups
    # -------------------------------------------------------------------------

    async def list_groups(
        self,
        *,
        user_id: str | None = None,
        external_id: str | None = None,
        query: str | None = None,
        offset: int | None = None,
        limit: int | None = None,
        sort: str | None = None,
        direction: SortDirection | str | None = None,
    ) -> GroupMembershipsResult:
        """
        List the groups in the workspace.

        Args:
            user_id: Limit to the groups this user belongs to.
            external_id: Match the group linked to this directory identifier.
            query: Match groups whose name contains this text.
            offset: How many records to skip.
            limit: How many records to return.
            sort: Field to order by.
            direction: `ASC` or `DESC`.

        Returns:
            GroupMembershipsResult: The groups, with the memberships that
                explain why each was returned.
        """
        return await self._run(
            group_ops.list_groups(
                user_id=user_id,
                external_id=external_id,
                query=query,
                offset=offset,
                limit=limit,
                sort=sort,
                direction=direction,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: get_group
    # -------------------------------------------------------------------------

    async def get_group(self, id: str) -> Group:
        """
        Retrieve one group.

        Returns:
            Group: The group.
        """
        return await self._run(group_ops.get_group(id))

    # -------------------------------------------------------------------------
    # METHOD: create_group
    # -------------------------------------------------------------------------

    async def create_group(self, name: str) -> Group:
        """
        Create a group.

        Returns:
            Group: The created group.
        """
        return await self._run(group_ops.create_group(name))

    # -------------------------------------------------------------------------
    # METHOD: update_group
    # -------------------------------------------------------------------------

    async def update_group(self, id: str, name: str) -> Group:
        """
        Rename a group.

        Returns:
            Group: The updated group.
        """
        return await self._run(group_ops.update_group(id, name))

    # -------------------------------------------------------------------------
    # METHOD: delete_group
    # -------------------------------------------------------------------------

    async def delete_group(self, id: str) -> bool:
        """
        Delete a group, removing the access it granted.

        Returns:
            bool: Whether the call succeeded.
        """
        return await self._run(group_ops.delete_group(id))

    # -------------------------------------------------------------------------
    # METHOD: list_group_users
    # -------------------------------------------------------------------------

    async def list_group_users(
        self,
        id: str,
        *,
        query: str | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> GroupMembershipsResult:
        """
        List the members of one group.

        Returns:
            GroupMembershipsResult: The users and their memberships.
        """
        return await self._run(
            group_ops.list_group_users(id, query=query, offset=offset, limit=limit)
        )

    # -------------------------------------------------------------------------
    # METHOD: add_group_user
    # -------------------------------------------------------------------------

    async def add_group_user(self, id: str, user_id: str) -> GroupMembershipsResult:
        """
        Add a user to a group.

        Returns:
            GroupMembershipsResult: The group, the user, and the new membership.
        """
        return await self._run(group_ops.add_group_user(id, user_id))

    # -------------------------------------------------------------------------
    # METHOD: update_group_user
    # -------------------------------------------------------------------------

    async def update_group_user(
        self,
        id: str,
        user_id: str,
        permission: str,
    ) -> GroupMembershipsResult:
        """
        Change a user's role within a group.

        Returns:
            GroupMembershipsResult: The group, the user, and the updated
                membership.
        """
        return await self._run(group_ops.update_group_user(id, user_id, permission))

    # -------------------------------------------------------------------------
    # METHOD: remove_group_user
    # -------------------------------------------------------------------------

    async def remove_group_user(self, id: str, user_id: str) -> GroupMembershipsResult:
        """
        Remove a user from a group.

        Returns:
            GroupMembershipsResult: The group as it now stands.
        """
        return await self._run(group_ops.remove_group_user(id, user_id))

    # -------------------------------------------------------------------------
    # METHOD: list_group_memberships
    # -------------------------------------------------------------------------

    async def list_group_memberships(
        self,
        *,
        group_id: str | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> GroupMembershipsResult:
        """
        List the documents shared with groups the calling user belongs to.

        Returns:
            GroupMembershipsResult: The memberships, with the groups and
                documents they refer to.
        """
        return await self._run(
            group_ops.list_group_memberships(
                group_id=group_id, offset=offset, limit=limit
            )
        )

    # =========================================================================
    # SECTION: Collections
    # =========================================================================

    # -------------------------------------------------------------------------
    # METHOD: list_collections
    # -------------------------------------------------------------------------

    async def list_collections(
        self,
        *,
        filters: list[CollectionFilterCondition | CollectionFilterGroup] | None = None,
        query: str | None = None,
        status_filter: list[CollectionStatus | str] | None = None,
        offset: int | None = None,
        limit: int | None = None,
        sort: str | None = None,
        direction: SortDirection | str | None = None,
    ) -> list[Collection]:
        """
        List the collections the calling user can see.

        Args:
            filters: Structured filter expression, evaluated as an AND of the
                top-level entries.
            query: Deprecated; prefer a `name` condition in `filters`.
            status_filter: Deprecated; prefer an `archivedAt` condition in
                `filters`.
            offset: How many records to skip.
            limit: How many records to return.
            sort: Field to order by.
            direction: `ASC` or `DESC`.

        Returns:
            list[Collection]: The matching collections.
        """
        return await self._run(
            collection_ops.list_collections(
                filters=filters,
                query=query,
                status_filter=status_filter,
                offset=offset,
                limit=limit,
                sort=sort,
                direction=direction,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: get_collection
    # -------------------------------------------------------------------------

    async def get_collection(self, id: str) -> Collection:
        """
        Retrieve one collection.

        Returns:
            Collection: The collection.
        """
        return await self._run(collection_ops.get_collection(id))

    # -------------------------------------------------------------------------
    # METHOD: get_collection_structure
    # -------------------------------------------------------------------------

    async def get_collection_structure(self, id: str) -> list[NavigationNode]:
        """
        Retrieve a collection's document tree.

        Each node carries the document's id, title, and its own children, so
        one call describes the whole hierarchy without a request per document.

        Returns:
            list[NavigationNode]: The top-level documents and their children.
        """
        return await self._run(collection_ops.get_collection_structure(id))

    # -------------------------------------------------------------------------
    # METHOD: create_collection
    # -------------------------------------------------------------------------

    async def create_collection(
        self,
        name: str,
        *,
        description: str | None = None,
        data: dict[str, Any] | None = None,
        permission: Permission | str | None = None,
        icon: str | None = None,
        color: str | None = None,
        sharing: bool | None = None,
    ) -> Collection:
        """
        Create a collection.

        Args:
            name: The collection's name.
            description: The description, as markdown.
            data: The description as a rich-text document; takes precedence
                over `description` when both are given.
            permission: The access every workspace member gets. Omitting it
                makes the collection private to its members.
            icon: An icon name from the `outline-icons` set.
            color: A hex color for the icon.
            sharing: Whether documents in it may be shared publicly.

        Returns:
            Collection: The created collection.
        """
        return await self._run(
            collection_ops.create_collection(
                name,
                description=description,
                data=data,
                permission=permission,
                icon=icon,
                color=color,
                sharing=sharing,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: update_collection
    # -------------------------------------------------------------------------

    async def update_collection(
        self,
        id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        data: dict[str, Any] | None = None,
        permission: Permission | str | None = None,
        icon: str | None = None,
        color: str | None = None,
        sharing: bool | None = None,
    ) -> Collection:
        """
        Update a collection, leaving the fields you omit as they are.

        Returns:
            Collection: The updated collection.
        """
        return await self._run(
            collection_ops.update_collection(
                id,
                name=name,
                description=description,
                data=data,
                permission=permission,
                icon=icon,
                color=color,
                sharing=sharing,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: delete_collection
    # -------------------------------------------------------------------------

    async def delete_collection(self, id: str) -> bool:
        """
        Delete a collection and every document in it.

        Returns:
            bool: Whether the call succeeded.
        """
        return await self._run(collection_ops.delete_collection(id))

    # -------------------------------------------------------------------------
    # METHOD: duplicate_collection
    # -------------------------------------------------------------------------

    async def duplicate_collection(
        self, id: str, *, name: str | None = None
    ) -> Collection:
        """
        Copy a collection and its documents into a new collection.

        Returns:
            Collection: The new collection.
        """
        return await self._run(collection_ops.duplicate_collection(id, name=name))

    # -------------------------------------------------------------------------
    # METHOD: archive_collection
    # -------------------------------------------------------------------------

    async def archive_collection(self, id: str) -> Collection:
        """
        Archive a collection, hiding it and its documents from search.

        Returns:
            Collection: The archived collection.
        """
        return await self._run(collection_ops.archive_collection(id))

    # -------------------------------------------------------------------------
    # METHOD: restore_collection
    # -------------------------------------------------------------------------

    async def restore_collection(self, id: str) -> Collection:
        """
        Restore an archived collection.

        Returns:
            Collection: The restored collection.
        """
        return await self._run(collection_ops.restore_collection(id))

    # -------------------------------------------------------------------------
    # METHOD: move_collection
    # -------------------------------------------------------------------------

    async def move_collection(self, id: str, index: str) -> CollectionIndex:
        """
        Reorder a collection in the sidebar.

        `index` is a fractional index - an opaque sortable string that places
        the collection between two neighbours without renumbering the rest.

        Returns:
            CollectionIndex: The index the collection now sorts at.
        """
        return await self._run(collection_ops.move_collection(id, index))

    # -------------------------------------------------------------------------
    # METHOD: list_collection_memberships
    # -------------------------------------------------------------------------

    async def list_collection_memberships(
        self,
        id: str,
        *,
        query: str | None = None,
        permission: Permission | str | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> MembershipsResult:
        """
        List the users given access to a collection individually.

        Returns:
            MembershipsResult: The users and their memberships.
        """
        return await self._run(
            collection_ops.list_collection_memberships(
                id,
                query=query,
                permission=permission,
                offset=offset,
                limit=limit,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: add_collection_user
    # -------------------------------------------------------------------------

    async def add_collection_user(
        self,
        id: str,
        user_id: str,
        *,
        permission: Permission | str | None = None,
    ) -> MembershipsResult:
        """
        Give one user access to a collection.

        Returns:
            MembershipsResult: The user and the new membership.
        """
        return await self._run(
            collection_ops.add_collection_user(id, user_id, permission=permission)
        )

    # -------------------------------------------------------------------------
    # METHOD: remove_collection_user
    # -------------------------------------------------------------------------

    async def remove_collection_user(self, id: str, user_id: str) -> bool:
        """
        Take away one user's individual access to a collection.

        Returns:
            bool: Whether the call succeeded.
        """
        return await self._run(collection_ops.remove_collection_user(id, user_id))

    # -------------------------------------------------------------------------
    # METHOD: list_collection_group_memberships
    # -------------------------------------------------------------------------

    async def list_collection_group_memberships(
        self,
        id: str,
        *,
        query: str | None = None,
        permission: Permission | str | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> CollectionGroupMembershipsResult:
        """
        List the groups given access to a collection.

        Returns:
            CollectionGroupMembershipsResult: The groups and their memberships.
        """
        return await self._run(
            collection_ops.list_collection_group_memberships(
                id,
                query=query,
                permission=permission,
                offset=offset,
                limit=limit,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: add_collection_group
    # -------------------------------------------------------------------------

    async def add_collection_group(
        self,
        id: str,
        group_id: str,
        *,
        permission: Permission | str | None = None,
    ) -> CollectionGroupMembershipsResult:
        """
        Give a group access to a collection.

        Returns:
            CollectionGroupMembershipsResult: The new membership.
        """
        return await self._run(
            collection_ops.add_collection_group(id, group_id, permission=permission)
        )

    # -------------------------------------------------------------------------
    # METHOD: remove_collection_group
    # -------------------------------------------------------------------------

    async def remove_collection_group(self, id: str, group_id: str) -> bool:
        """
        Take away a group's access to a collection.

        Returns:
            bool: Whether the call succeeded.
        """
        return await self._run(collection_ops.remove_collection_group(id, group_id))

    # -------------------------------------------------------------------------
    # METHOD: export_collection
    # -------------------------------------------------------------------------

    async def export_collection(
        self,
        id: str,
        *,
        format: str | None = None,
    ) -> FileOperationResult:
        """
        Start an export of one collection.

        The export runs in the background. Poll `get_file_operation` until the
        returned operation reaches `complete`, then fetch the archive with
        `download_file_operation`.

        Args:
            id: The collection to export.
            format: `outline-markdown`, `json`, or `html`.

        Returns:
            FileOperationResult: The queued export.
        """
        return await self._run(collection_ops.export_collection(id, format=format))

    # -------------------------------------------------------------------------
    # METHOD: export_all_collections
    # -------------------------------------------------------------------------

    async def export_all_collections(
        self,
        *,
        format: str | None = None,
        include_attachments: bool | None = None,
        include_private: bool | None = None,
    ) -> FileOperationResult:
        """
        Start an export of every collection the calling user can see.

        Returns:
            FileOperationResult: The queued export.
        """
        return await self._run(
            collection_ops.export_all_collections(
                format=format,
                include_attachments=include_attachments,
                include_private=include_private,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: import_collection
    # -------------------------------------------------------------------------

    async def import_collection(
        self,
        attachment_id: str,
        *,
        format: str | None = None,
        permission: Permission | str | None = None,
    ) -> FileOperationResult:
        """
        Create a collection from a file uploaded through `create_attachment`.

        Returns:
            FileOperationResult: The queued import.
        """
        return await self._run(
            collection_ops.import_collection(
                attachment_id, format=format, permission=permission
            )
        )

    # =========================================================================
    # SECTION: Documents
    # =========================================================================

    # -------------------------------------------------------------------------
    # METHOD: list_documents
    # -------------------------------------------------------------------------

    async def list_documents(
        self,
        *,
        filters: document_ops.DocumentFilters | None = None,
        backlink_document_id: str | None = None,
        collection_id: str | None = None,
        user_id: str | None = None,
        parent_document_id: str | None = None,
        status_filter: list[str] | None = None,
        offset: int | None = None,
        limit: int | None = None,
        sort: str | None = None,
        direction: SortDirection | str | None = None,
    ) -> list[Document]:
        """
        List the published documents and the calling user's own drafts.

        Args:
            filters: Structured filter expression, evaluated as an AND of the
                top-level entries. Cannot be combined with the deprecated
                arguments below.
            backlink_document_id: Limit to documents that link to this one.
            collection_id: Deprecated; prefer a `collectionId` condition.
            user_id: Deprecated; prefer a `userId` condition.
            parent_document_id: Deprecated; prefer a `parentDocumentId`
                condition.
            status_filter: Deprecated; prefer a status condition.
            offset: How many records to skip.
            limit: How many records to return.
            sort: Field to order by.
            direction: `ASC` or `DESC`.

        Returns:
            list[Document]: The matching documents.
        """
        return await self._run(
            document_ops.list_documents(
                filters=filters,
                backlink_document_id=backlink_document_id,
                collection_id=collection_id,
                user_id=user_id,
                parent_document_id=parent_document_id,
                status_filter=status_filter,
                offset=offset,
                limit=limit,
                sort=sort,
                direction=direction,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: get_document
    # -------------------------------------------------------------------------

    async def get_document(
        self,
        id: str | None = None,
        *,
        share_id: str | None = None,
    ) -> Document:
        """
        Retrieve one document by id, url id, or share id.

        At least one of `id` and `share_id` must be given. A `share_id` reads
        a publicly shared document, which Outline serves without a token.

        Returns:
            Document: The document.
        """
        return await self._run(document_ops.get_document(id, share_id=share_id))

    # -------------------------------------------------------------------------
    # METHOD: get_document_structure
    # -------------------------------------------------------------------------

    async def get_document_structure(self, id: str) -> NavigationNode:
        """
        Retrieve a document and its nested children as a tree.

        Returns:
            NavigationNode: The document, with its children.
        """
        return await self._run(document_ops.get_document_structure(id))

    # -------------------------------------------------------------------------
    # METHOD: create_document
    # -------------------------------------------------------------------------

    async def create_document(
        self,
        *,
        id: str | None = None,
        title: str | None = None,
        text: str | None = None,
        icon: str | None = None,
        color: str | None = None,
        collection_id: str | None = None,
        parent_document_id: str | None = None,
        template_id: str | None = None,
        publish: bool | None = None,
        full_width: bool | None = None,
        preferences: DocumentPreferences | None = None,
        created_at: datetime | str | None = None,
        data_attributes: list[DocumentDataAttribute] | None = None,
    ) -> Document:
        """
        Create a document.

        A document is created as a draft unless `publish` is set, and a draft
        needs no collection. Publishing requires one, either directly through
        `collection_id` or by inheriting it from `parent_document_id`.

        Args:
            id: A UUID to create the document under, so a retry of a failed
                create does not produce a second document.
            title: The document's title.
            text: The body, as markdown.
            icon: An icon name from the `outline-icons` set, or an emoji.
            color: A hex color for the icon.
            collection_id: The collection to publish into.
            parent_document_id: The document to nest this one under.
            template_id: A template to prefill the body from.
            publish: Whether to publish rather than leave it a draft.
            full_width: Whether to render edge to edge.
            preferences: Document-level display preferences.
            created_at: Backdate the document; admin only.
            data_attributes: Values for the workspace's custom attributes.

        Returns:
            Document: The created document.
        """
        return await self._run(
            document_ops.create_document(
                id=id,
                title=title,
                text=text,
                icon=icon,
                color=color,
                collection_id=collection_id,
                parent_document_id=parent_document_id,
                template_id=template_id,
                publish=publish,
                full_width=full_width,
                preferences=preferences,
                created_at=created_at,
                data_attributes=data_attributes,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: update_document
    # -------------------------------------------------------------------------

    async def update_document(
        self,
        id: str,
        *,
        title: str | None = None,
        text: str | None = None,
        icon: str | None = None,
        color: str | None = None,
        full_width: bool | None = None,
        preferences: DocumentPreferences | None = None,
        template_id: str | None = None,
        collection_id: str | None = None,
        insights_enabled: bool | None = None,
        edit_mode: TextEditMode | str | None = None,
        find_text: str | None = None,
        publish: bool | None = None,
        last_revision: int | None = None,
        data_attributes: list[DocumentDataAttribute] | None = None,
    ) -> Document:
        """
        Update a document, leaving the fields you omit as they are.

        `text` replaces the whole body by default. `edit_mode` changes that:
        `append` and `prepend` add to it, and `patch` replaces the occurrence
        of `find_text` with `text`.

        `last_revision` guards against a lost update - pass the revision you
        read and Outline rejects the write if the document has moved on since.

        Returns:
            Document: The updated document.
        """
        return await self._run(
            document_ops.update_document(
                id,
                title=title,
                text=text,
                icon=icon,
                color=color,
                full_width=full_width,
                preferences=preferences,
                template_id=template_id,
                collection_id=collection_id,
                insights_enabled=insights_enabled,
                edit_mode=edit_mode,
                find_text=find_text,
                publish=publish,
                last_revision=last_revision,
                data_attributes=data_attributes,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: delete_document
    # -------------------------------------------------------------------------

    async def delete_document(self, id: str, *, permanent: bool | None = None) -> bool:
        """
        Move a document to the trash, or delete it outright.

        Returns:
            bool: Whether the call succeeded.
        """
        return await self._run(document_ops.delete_document(id, permanent=permanent))

    # -------------------------------------------------------------------------
    # METHOD: move_document
    # -------------------------------------------------------------------------

    async def move_document(
        self,
        id: str,
        *,
        collection_id: str | None = None,
        parent_document_id: str | None = None,
        index: float | None = None,
    ) -> DocumentMoveResult:
        """
        Move a document to another collection or under another parent.

        Returns:
            DocumentMoveResult: The documents that moved and the collections
                whose structure changed.
        """
        return await self._run(
            document_ops.move_document(
                id,
                collection_id=collection_id,
                parent_document_id=parent_document_id,
                index=index,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: duplicate_document
    # -------------------------------------------------------------------------

    async def duplicate_document(
        self,
        id: str,
        *,
        title: str | None = None,
        recursive: bool | None = None,
        publish: bool | None = None,
        collection_id: str | None = None,
        parent_document_id: str | None = None,
    ) -> DocumentsResult:
        """
        Copy a document, optionally with its children.

        Returns:
            DocumentsResult: The documents that were created.
        """
        return await self._run(
            document_ops.duplicate_document(
                id,
                title=title,
                recursive=recursive,
                publish=publish,
                collection_id=collection_id,
                parent_document_id=parent_document_id,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: archive_document
    # -------------------------------------------------------------------------

    async def archive_document(self, id: str) -> Document:
        """
        Archive a document, hiding it from its collection and from search.

        Returns:
            Document: The archived document.
        """
        return await self._run(document_ops.archive_document(id))

    # -------------------------------------------------------------------------
    # METHOD: restore_document
    # -------------------------------------------------------------------------

    async def restore_document(
        self,
        id: str,
        *,
        collection_id: str | None = None,
        revision_id: str | None = None,
    ) -> Document:
        """
        Restore a document from the archive or the trash.

        Passing `revision_id` rolls the document's contents back to that
        revision instead.

        Returns:
            Document: The restored document.
        """
        return await self._run(
            document_ops.restore_document(
                id, collection_id=collection_id, revision_id=revision_id
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: unpublish_document
    # -------------------------------------------------------------------------

    async def unpublish_document(
        self, id: str, *, detach: bool | None = None
    ) -> Document:
        """
        Return a published document to the draft state.

        Returns:
            Document: The unpublished document.
        """
        return await self._run(document_ops.unpublish_document(id, detach=detach))

    # -------------------------------------------------------------------------
    # METHOD: templatize_document
    # -------------------------------------------------------------------------

    async def templatize_document(
        self,
        id: str,
        publish: bool,
        *,
        collection_id: str | None = None,
    ) -> Template:
        """
        Create a template from a document's contents.

        Returns:
            Template: The created template.
        """
        return await self._run(
            document_ops.templatize_document(id, publish, collection_id=collection_id)
        )

    # -------------------------------------------------------------------------
    # METHOD: empty_trash
    # -------------------------------------------------------------------------

    async def empty_trash(self) -> bool:
        """
        Permanently delete every document in the trash.

        Returns:
            bool: Whether the call succeeded.
        """
        return await self._run(document_ops.empty_trash())

    # -------------------------------------------------------------------------
    # METHOD: list_archived_documents
    # -------------------------------------------------------------------------

    async def list_archived_documents(
        self,
        *,
        collection_id: str | None = None,
        offset: int | None = None,
        limit: int | None = None,
        sort: str | None = None,
        direction: SortDirection | str | None = None,
    ) -> list[Document]:
        """
        List the archived documents.

        Returns:
            list[Document]: The archived documents.
        """
        return await self._run(
            document_ops.list_archived_documents(
                collection_id=collection_id,
                offset=offset,
                limit=limit,
                sort=sort,
                direction=direction,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: list_deleted_documents
    # -------------------------------------------------------------------------

    async def list_deleted_documents(
        self,
        *,
        filters: document_ops.DeletedFilters | None = None,
        offset: int | None = None,
        limit: int | None = None,
        sort: str | None = None,
        direction: SortDirection | str | None = None,
    ) -> list[Document]:
        """
        List the documents in the trash.

        Returns:
            list[Document]: The deleted documents.
        """
        return await self._run(
            document_ops.list_deleted_documents(
                filters=filters,
                offset=offset,
                limit=limit,
                sort=sort,
                direction=direction,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: list_draft_documents
    # -------------------------------------------------------------------------

    async def list_draft_documents(
        self,
        *,
        collection_id: str | None = None,
        date_filter: str | None = None,
        offset: int | None = None,
        limit: int | None = None,
        sort: str | None = None,
        direction: SortDirection | str | None = None,
    ) -> list[Document]:
        """
        List the calling user's unpublished drafts.

        Returns:
            list[Document]: The draft documents.
        """
        return await self._run(
            document_ops.list_draft_documents(
                collection_id=collection_id,
                date_filter=date_filter,
                offset=offset,
                limit=limit,
                sort=sort,
                direction=direction,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: list_viewed_documents
    # -------------------------------------------------------------------------

    async def list_viewed_documents(
        self,
        *,
        offset: int | None = None,
        limit: int | None = None,
        sort: str | None = None,
        direction: SortDirection | str | None = None,
    ) -> list[Document]:
        """
        List the documents the calling user viewed most recently.

        Returns:
            list[Document]: The recently viewed documents.
        """
        return await self._run(
            document_ops.list_viewed_documents(
                offset=offset, limit=limit, sort=sort, direction=direction
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: search_documents
    # -------------------------------------------------------------------------

    async def search_documents(
        self,
        query: str | None = None,
        *,
        filters: document_ops.DocumentFilters | None = None,
        collection_id: str | None = None,
        document_id: str | None = None,
        user_id: str | None = None,
        status_filter: list[str] | None = None,
        date_filter: str | None = None,
        share_id: str | None = None,
        snippet_min_words: int | None = None,
        snippet_max_words: int | None = None,
        offset: int | None = None,
        limit: int | None = None,
        sort: str | None = None,
        direction: SortDirection | str | None = None,
    ) -> list[SearchHit]:
        """
        Search documents by their full contents.

        Omitting `query` lists documents matching the filters alone, ordered
        by `sort` rather than by relevance.

        Returns:
            list[SearchHit]: The matches, each with the document and the
                snippet of text that matched.
        """
        return await self._run(
            document_ops.search_documents(
                query,
                filters=filters,
                collection_id=collection_id,
                document_id=document_id,
                user_id=user_id,
                status_filter=status_filter,
                date_filter=date_filter,
                share_id=share_id,
                snippet_min_words=snippet_min_words,
                snippet_max_words=snippet_max_words,
                offset=offset,
                limit=limit,
                sort=sort,
                direction=direction,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: search_document_titles
    # -------------------------------------------------------------------------

    async def search_document_titles(
        self,
        query: str,
        *,
        filters: document_ops.DocumentFilters | None = None,
        collection_id: str | None = None,
        document_id: str | None = None,
        user_id: str | None = None,
        status_filter: list[str] | None = None,
        date_filter: str | None = None,
        share_id: str | None = None,
        offset: int | None = None,
        limit: int | None = None,
        sort: str | None = None,
        direction: SortDirection | str | None = None,
    ) -> list[Document]:
        """
        Search documents by title alone.

        Returns:
            list[Document]: The matching documents.
        """
        return await self._run(
            document_ops.search_document_titles(
                query,
                filters=filters,
                collection_id=collection_id,
                document_id=document_id,
                user_id=user_id,
                status_filter=status_filter,
                date_filter=date_filter,
                share_id=share_id,
                offset=offset,
                limit=limit,
                sort=sort,
                direction=direction,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: answer_question
    # -------------------------------------------------------------------------

    async def answer_question(
        self,
        query: str,
        *,
        collection_id: str | None = None,
        document_id: str | None = None,
        user_id: str | None = None,
        status_filter: str | None = None,
        date_filter: str | None = None,
    ) -> AnswerResult:
        """
        Ask a natural-language question of the workspace's documents.

        Available only on installations with the AI answers feature enabled;
        elsewhere Outline answers this with a 402.

        Returns:
            AnswerResult: The answer, and the documents it was drawn from.
        """
        return await self._run(
            document_ops.answer_question(
                query,
                collection_id=collection_id,
                document_id=document_id,
                user_id=user_id,
                status_filter=status_filter,
                date_filter=date_filter,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: export_document
    # -------------------------------------------------------------------------

    async def export_document(
        self,
        id: str,
        *,
        paper_size: str | None = None,
        signed_urls: int | None = None,
        include_child_documents: bool | None = None,
    ) -> str:
        """
        Export one document as markdown.

        Use `download_document` for the PDF, HTML, and TextBundle formats,
        which come back as bytes rather than text.

        Args:
            id: The document to export.
            paper_size: Page size, which only applies to a PDF export.
            signed_urls: How long, in seconds, the signed links to attachments
                should remain valid.
            include_child_documents: Include nested documents, which makes the
                export a zip archive and so requires `download_document`.

        Returns:
            str: The document as markdown.
        """
        return await self._run(
            document_ops.export_document(
                id,
                paper_size=paper_size,
                signed_urls=signed_urls,
                include_child_documents=include_child_documents,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: download_document
    # -------------------------------------------------------------------------

    async def download_document(
        self,
        id: str,
        *,
        accept: str = "application/pdf",
        paper_size: str | None = None,
        signed_urls: int | None = None,
        include_child_documents: bool | None = None,
    ) -> bytes:
        """
        Export one document in a binary format.

        The same method as `export_document`, asked for a different
        representation: Outline picks the format from the `Accept` header, so
        `application/pdf`, `text/html`, and `application/x-textbundle` are all
        reachable here. `text/markdown` works too, though `export_document` is
        the more convenient way to ask for it.

        Returns:
            bytes: The exported file.
        """
        operation = document_ops.export_document(
            id,
            paper_size=paper_size,
            signed_urls=signed_urls,
            include_child_documents=include_child_documents,
        )

        return await self._download(operation.path, operation.payload, accept)

    # -------------------------------------------------------------------------
    # METHOD: import_document
    # -------------------------------------------------------------------------

    async def import_document(
        self,
        file: bytes | IO[bytes],
        *,
        filename: str,
        content_type: str | None = None,
        collection_id: str | None = None,
        parent_document_id: str | None = None,
        publish: bool | None = None,
    ) -> Document:
        """
        Create a document by uploading a file.

        Markdown, plain text, docx, PDF, csv, tsv, HTML, MHTML, eml, and
        TextBundle files are accepted. One of `collection_id` and
        `parent_document_id` is required.

        Args:
            file: The file contents, as bytes or an open binary file.
            filename: The name to upload it under, whose extension is what
                Outline uses to decide how to parse it.
            content_type: The MIME type, if the extension is not enough.
            collection_id: The collection to import into.
            parent_document_id: The document to import under.
            publish: Whether to publish rather than leave it a draft.

        Returns:
            Document: The imported document.
        """
        operation = document_ops.import_document(
            collection_id=collection_id,
            parent_document_id=parent_document_id,
            publish=publish,
        )
        url = self._endpoint(operation.path)
        logger.info("POST %s", url)

        response = await self._http.post(
            url=url,
            files={"file": (filename, file, content_type)},
            data=form_fields(operation.payload),
            headers=self._headers(),
            timeout=self._request_timeout(),
        )

        return operation.parse(self._decode(response))

    # -------------------------------------------------------------------------
    # METHOD: list_document_insights
    # -------------------------------------------------------------------------

    async def list_document_insights(
        self,
        id: str,
        *,
        start_date: date | str | None = None,
        end_date: date | str | None = None,
    ) -> list[DocumentInsight]:
        """
        Retrieve the daily and weekly activity rollups for a document.

        Returns:
            list[DocumentInsight]: The rollups, one per period.
        """
        return await self._run(
            document_ops.list_document_insights(
                id, start_date=start_date, end_date=end_date
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: list_document_users
    # -------------------------------------------------------------------------

    async def list_document_users(
        self,
        id: str,
        *,
        query: str | None = None,
        user_id: str | None = None,
    ) -> list[User]:
        """
        List the users who can access a document, however they got access.

        Returns:
            list[User]: The users with access.
        """
        return await self._run(
            document_ops.list_document_users(id, query=query, user_id=user_id)
        )

    # -------------------------------------------------------------------------
    # METHOD: list_document_memberships
    # -------------------------------------------------------------------------

    async def list_document_memberships(
        self,
        id: str,
        *,
        query: str | None = None,
        permission: Permission | str | None = None,
    ) -> MembershipsResult:
        """
        List the users given access to a document individually.

        Returns:
            MembershipsResult: The users and their memberships.
        """
        return await self._run(
            document_ops.list_document_memberships(
                id, query=query, permission=permission
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: add_document_user
    # -------------------------------------------------------------------------

    async def add_document_user(
        self,
        id: str,
        user_id: str,
        *,
        permission: Permission | str | None = None,
    ) -> MembershipsResult:
        """
        Give one user access to a document.

        Returns:
            MembershipsResult: The user and the new membership.
        """
        return await self._run(
            document_ops.add_document_user(id, user_id, permission=permission)
        )

    # -------------------------------------------------------------------------
    # METHOD: remove_document_user
    # -------------------------------------------------------------------------

    async def remove_document_user(self, id: str, user_id: str) -> bool:
        """
        Take away one user's individual access to a document.

        Returns:
            bool: Whether the call succeeded.
        """
        return await self._run(document_ops.remove_document_user(id, user_id))

    # -------------------------------------------------------------------------
    # METHOD: list_document_group_memberships
    # -------------------------------------------------------------------------

    async def list_document_group_memberships(
        self,
        id: str,
        *,
        query: str | None = None,
        permission: Permission | str | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> DocumentGroupMembershipsResult:
        """
        List the groups given access to a document.

        Returns:
            DocumentGroupMembershipsResult: The groups and their memberships.
        """
        return await self._run(
            document_ops.list_document_group_memberships(
                id,
                query=query,
                permission=permission,
                offset=offset,
                limit=limit,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: add_document_group
    # -------------------------------------------------------------------------

    async def add_document_group(
        self,
        id: str,
        group_id: str,
        *,
        permission: Permission | str | None = None,
    ) -> DocumentGroupMembershipsResult:
        """
        Give a group access to a document.

        Returns:
            DocumentGroupMembershipsResult: The new membership.
        """
        return await self._run(
            document_ops.add_document_group(id, group_id, permission=permission)
        )

    # -------------------------------------------------------------------------
    # METHOD: remove_document_group
    # -------------------------------------------------------------------------

    async def remove_document_group(self, id: str, group_id: str) -> bool:
        """
        Take away a group's access to a document.

        Returns:
            bool: Whether the call succeeded.
        """
        return await self._run(document_ops.remove_document_group(id, group_id))

    # =========================================================================
    # SECTION: Templates
    # =========================================================================

    # -------------------------------------------------------------------------
    # METHOD: list_templates
    # -------------------------------------------------------------------------

    async def list_templates(
        self,
        *,
        collection_id: str | None = None,
        query: str | None = None,
        offset: int | None = None,
        limit: int | None = None,
        sort: str | None = None,
        direction: SortDirection | str | None = None,
    ) -> list[Template]:
        """
        List the templates the calling user can see.

        Returns:
            list[Template]: The matching templates.
        """
        return await self._run(
            template_ops.list_templates(
                collection_id=collection_id,
                query=query,
                offset=offset,
                limit=limit,
                sort=sort,
                direction=direction,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: get_template
    # -------------------------------------------------------------------------

    async def get_template(self, id: str) -> Template:
        """
        Retrieve one template.

        Returns:
            Template: The template.
        """
        return await self._run(template_ops.get_template(id))

    # -------------------------------------------------------------------------
    # METHOD: create_template
    # -------------------------------------------------------------------------

    async def create_template(
        self,
        *,
        id: str | None = None,
        title: str | None = None,
        data: dict[str, Any] | None = None,
        icon: str | None = None,
        color: str | None = None,
        collection_id: str | None = None,
        publish: bool | None = None,
    ) -> Template:
        """
        Create a template.

        Omitting `collection_id` makes the template available across the whole
        workspace rather than within one collection.

        Returns:
            Template: The created template.
        """
        return await self._run(
            template_ops.create_template(
                id=id,
                title=title,
                data=data,
                icon=icon,
                color=color,
                collection_id=collection_id,
                publish=publish,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: update_template
    # -------------------------------------------------------------------------

    async def update_template(
        self,
        id: str,
        *,
        title: str | None = None,
        data: dict[str, Any] | None = None,
        icon: str | None = None,
        color: str | None = None,
        full_width: bool | None = None,
        collection_id: str | None = None,
        publish: bool | None = None,
    ) -> Template:
        """
        Update a template, leaving the fields you omit as they are.

        Returns:
            Template: The updated template.
        """
        return await self._run(
            template_ops.update_template(
                id,
                title=title,
                data=data,
                icon=icon,
                color=color,
                full_width=full_width,
                collection_id=collection_id,
                publish=publish,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: duplicate_template
    # -------------------------------------------------------------------------

    async def duplicate_template(
        self,
        id: str,
        *,
        title: str | None = None,
        collection_id: str | None = None,
    ) -> Template:
        """
        Copy a template.

        Returns:
            Template: The new template.
        """
        return await self._run(
            template_ops.duplicate_template(
                id, title=title, collection_id=collection_id
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: restore_template
    # -------------------------------------------------------------------------

    async def restore_template(self, id: str) -> Template:
        """
        Restore a deleted template.

        Returns:
            Template: The restored template.
        """
        return await self._run(template_ops.restore_template(id))

    # -------------------------------------------------------------------------
    # METHOD: delete_template
    # -------------------------------------------------------------------------

    async def delete_template(self, id: str) -> bool:
        """
        Delete a template.

        Returns:
            bool: Whether the call succeeded.
        """
        return await self._run(template_ops.delete_template(id))

    # =========================================================================
    # SECTION: Comments
    # =========================================================================

    # -------------------------------------------------------------------------
    # METHOD: list_comments
    # -------------------------------------------------------------------------

    async def list_comments(
        self,
        *,
        document_id: str | None = None,
        collection_id: str | None = None,
        parent_comment_id: str | None = None,
        status_filter: list[CommentStatusFilter | str] | None = None,
        include_anchor_text: bool | None = None,
        offset: int | None = None,
        limit: int | None = None,
        sort: str | None = None,
        direction: SortDirection | str | None = None,
    ) -> list[Comment]:
        """
        List comments on a document or across a collection.

        Args:
            document_id: Limit to the comments on one document.
            collection_id: Limit to the comments across one collection.
            parent_comment_id: Limit to the replies under this comment.
            status_filter: Limit to `resolved` or `unresolved` threads.
                Passing both, or neither, returns every comment.
            include_anchor_text: Include the passage each inline comment is
                attached to.
            offset: How many records to skip.
            limit: How many records to return.
            sort: Field to order by.
            direction: `ASC` or `DESC`.

        Returns:
            list[Comment]: The matching comments.
        """
        return await self._run(
            comment_ops.list_comments(
                document_id=document_id,
                collection_id=collection_id,
                parent_comment_id=parent_comment_id,
                status_filter=status_filter,
                include_anchor_text=include_anchor_text,
                offset=offset,
                limit=limit,
                sort=sort,
                direction=direction,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: get_comment
    # -------------------------------------------------------------------------

    async def get_comment(
        self,
        id: str,
        *,
        include_anchor_text: bool | None = None,
    ) -> Comment:
        """
        Retrieve one comment.

        Returns:
            Comment: The comment.
        """
        return await self._run(
            comment_ops.get_comment(id, include_anchor_text=include_anchor_text)
        )

    # -------------------------------------------------------------------------
    # METHOD: create_comment
    # -------------------------------------------------------------------------

    async def create_comment(
        self,
        document_id: str,
        *,
        id: str | None = None,
        parent_comment_id: str | None = None,
        data: dict[str, Any] | None = None,
        text: str | None = None,
        anchor_text: str | None = None,
        anchor_prefix: str | None = None,
        anchor_suffix: str | None = None,
    ) -> Comment:
        """
        Comment on a document, or reply to an existing comment.

        Args:
            document_id: The document to comment on.
            id: A UUID to create the comment under, so a retry of a failed
                create does not produce a second comment.
            parent_comment_id: The comment this one replies to.
            data: The comment body as a rich-text document.
            text: The comment body as markdown, if `data` is not given.
            anchor_text: The passage in the document this comment is attached
                to, which makes it an inline comment rather than a thread.
            anchor_prefix: The text immediately before `anchor_text`, used to
                relocate the anchor when the document changes.
            anchor_suffix: The text immediately after `anchor_text`.

        Returns:
            Comment: The created comment.
        """
        return await self._run(
            comment_ops.create_comment(
                document_id,
                id=id,
                parent_comment_id=parent_comment_id,
                data=data,
                text=text,
                anchor_text=anchor_text,
                anchor_prefix=anchor_prefix,
                anchor_suffix=anchor_suffix,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: update_comment
    # -------------------------------------------------------------------------

    async def update_comment(
        self,
        id: str,
        data: dict[str, Any] | None = None,
        *,
        text: str | None = None,
    ) -> Comment:
        """
        Replace a comment's body.

        Give the new body as `data` or as `text`; Outline rejects a call that
        has neither.

        Args:
            id: The comment to update.
            data: The new body as a rich-text document.
            text: The new body as markdown, if `data` is not given. Needs an
                Outline release after v1.10.1; an older server answers with
                `ValidationError`.

        Returns:
            Comment: The updated comment.
        """
        return await self._run(comment_ops.update_comment(id, data, text=text))

    # -------------------------------------------------------------------------
    # METHOD: delete_comment
    # -------------------------------------------------------------------------

    async def delete_comment(self, id: str) -> bool:
        """
        Delete a comment and its replies.

        Returns:
            bool: Whether the call succeeded.
        """
        return await self._run(comment_ops.delete_comment(id))

    # -------------------------------------------------------------------------
    # METHOD: resolve_comment
    # -------------------------------------------------------------------------

    async def resolve_comment(self, id: str) -> Comment:
        """
        Mark a comment thread resolved.

        Returns:
            Comment: The resolved comment.
        """
        return await self._run(comment_ops.resolve_comment(id))

    # -------------------------------------------------------------------------
    # METHOD: unresolve_comment
    # -------------------------------------------------------------------------

    async def unresolve_comment(self, id: str) -> Comment:
        """
        Reopen a resolved comment thread.

        Returns:
            Comment: The reopened comment.
        """
        return await self._run(comment_ops.unresolve_comment(id))

    # -------------------------------------------------------------------------
    # METHOD: add_comment_reaction
    # -------------------------------------------------------------------------

    async def add_comment_reaction(self, id: str, emoji: str) -> bool:
        """
        React to a comment with an emoji.

        Returns:
            bool: Whether the call succeeded.
        """
        return await self._run(comment_ops.add_comment_reaction(id, emoji))

    # -------------------------------------------------------------------------
    # METHOD: remove_comment_reaction
    # -------------------------------------------------------------------------

    async def remove_comment_reaction(self, id: str, emoji: str) -> bool:
        """
        Take back an emoji reaction on a comment.

        Returns:
            bool: Whether the call succeeded.
        """
        return await self._run(comment_ops.remove_comment_reaction(id, emoji))

    # -------------------------------------------------------------------------
    # METHOD: list_reactions
    # -------------------------------------------------------------------------

    async def list_reactions(
        self,
        comment_id: str,
        *,
        offset: int | None = None,
        limit: int | None = None,
    ) -> list[Reaction]:
        """
        List the emoji reactions on a comment, with who left each one.

        Returns:
            list[Reaction]: The reactions.
        """
        return await self._run(
            reaction_ops.list_reactions(comment_id, offset=offset, limit=limit)
        )

    # =========================================================================
    # SECTION: Revisions
    # =========================================================================

    # -------------------------------------------------------------------------
    # METHOD: list_revisions
    # -------------------------------------------------------------------------

    async def list_revisions(
        self,
        document_id: str,
        *,
        offset: int | None = None,
        limit: int | None = None,
        sort: str | None = None,
        direction: SortDirection | str | None = None,
    ) -> list[Revision]:
        """
        List a document's revision history.

        The specification marks `document_id` optional, but Outline rejects the
        call without it, so it is required here.

        Returns:
            list[Revision]: The revisions, without their contents.
        """
        return await self._run(
            revision_ops.list_revisions(
                document_id,
                offset=offset,
                limit=limit,
                sort=sort,
                direction=direction,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: get_revision
    # -------------------------------------------------------------------------

    async def get_revision(self, id: str) -> RevisionDetail:
        """
        Retrieve one revision, including the document text it captured.

        Returns:
            RevisionDetail: The revision and its contents.
        """
        return await self._run(revision_ops.get_revision(id))

    # -------------------------------------------------------------------------
    # METHOD: update_revision
    # -------------------------------------------------------------------------

    async def update_revision(self, id: str, name: str) -> Revision:
        """
        Name a revision, so it can be found again in the history.

        Returns:
            Revision: The updated revision.
        """
        return await self._run(revision_ops.update_revision(id, name))

    # -------------------------------------------------------------------------
    # METHOD: delete_revision
    # -------------------------------------------------------------------------

    async def delete_revision(self, id: str) -> bool:
        """
        Delete a revision from a document's history.

        Returns:
            bool: Whether the call succeeded.
        """
        return await self._run(revision_ops.delete_revision(id))

    # -------------------------------------------------------------------------
    # METHOD: export_revision
    # -------------------------------------------------------------------------

    async def export_revision(self, id: str) -> FileOperationResult:
        """
        Start an export of one revision.

        Returns:
            FileOperationResult: The queued export.
        """
        return await self._run(revision_ops.export_revision(id))

    # =========================================================================
    # SECTION: Shares
    # =========================================================================

    # -------------------------------------------------------------------------
    # METHOD: list_shares
    # -------------------------------------------------------------------------

    async def list_shares(
        self,
        *,
        query: str | None = None,
        offset: int | None = None,
        limit: int | None = None,
        sort: str | None = None,
        direction: SortDirection | str | None = None,
    ) -> list[Share]:
        """
        List the share links the calling user can see.

        Returns:
            list[Share]: The matching shares.
        """
        return await self._run(
            share_ops.list_shares(
                query=query,
                offset=offset,
                limit=limit,
                sort=sort,
                direction=direction,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: get_share
    # -------------------------------------------------------------------------

    async def get_share(
        self,
        id: str | None = None,
        *,
        document_id: str | None = None,
    ) -> Share:
        """
        Retrieve one share, by its own id or by the document it shares.

        Returns:
            Share: The share.
        """
        return await self._run(share_ops.get_share(id, document_id=document_id))

    # -------------------------------------------------------------------------
    # METHOD: create_share
    # -------------------------------------------------------------------------

    async def create_share(
        self,
        *,
        document_id: str | None = None,
        collection_id: str | None = None,
    ) -> Share:
        """
        Create a share link for a document or a collection.

        Exactly one of `document_id` and `collection_id` is required. A share
        is created unpublished; call `update_share` with `published=True` to
        make it reachable without signing in. Asking twice for the same
        resource with the same token returns the share that already exists.

        Returns:
            Share: The share.
        """
        return await self._run(
            share_ops.create_share(document_id=document_id, collection_id=collection_id)
        )

    # -------------------------------------------------------------------------
    # METHOD: update_share
    # -------------------------------------------------------------------------

    async def update_share(
        self,
        id: str,
        published: bool,
        *,
        title: str | None = None,
        icon_url: str | None = None,
    ) -> Share:
        """
        Publish or unpublish a share, and set how it presents itself.

        Returns:
            Share: The updated share.
        """
        return await self._run(
            share_ops.update_share(id, published, title=title, icon_url=icon_url)
        )

    # -------------------------------------------------------------------------
    # METHOD: revoke_share
    # -------------------------------------------------------------------------

    async def revoke_share(self, id: str) -> bool:
        """
        Revoke a share link, so the URL stops working.

        Returns:
            bool: Whether the call succeeded.
        """
        return await self._run(share_ops.revoke_share(id))

    # =========================================================================
    # SECTION: Stars and pins
    # =========================================================================

    # -------------------------------------------------------------------------
    # METHOD: list_stars
    # -------------------------------------------------------------------------

    async def list_stars(
        self,
        *,
        offset: int | None = None,
        limit: int | None = None,
    ) -> StarsResult:
        """
        List the calling user's starred documents and collections.

        Returns:
            StarsResult: The stars and the documents they point at.
        """
        return await self._run(star_ops.list_stars(offset=offset, limit=limit))

    # -------------------------------------------------------------------------
    # METHOD: create_star
    # -------------------------------------------------------------------------

    async def create_star(
        self,
        *,
        document_id: str | None = None,
        collection_id: str | None = None,
        index: str | None = None,
    ) -> Star:
        """
        Star a document or a collection for the calling user.

        Returns:
            Star: The created star.
        """
        return await self._run(
            star_ops.create_star(
                document_id=document_id, collection_id=collection_id, index=index
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: update_star
    # -------------------------------------------------------------------------

    async def update_star(self, id: str, index: str) -> Star:
        """
        Reorder a star in the sidebar.

        Returns:
            Star: The updated star.
        """
        return await self._run(star_ops.update_star(id, index))

    # -------------------------------------------------------------------------
    # METHOD: delete_star
    # -------------------------------------------------------------------------

    async def delete_star(self, id: str) -> bool:
        """
        Remove a star.

        Returns:
            bool: Whether the call succeeded.
        """
        return await self._run(star_ops.delete_star(id))

    # -------------------------------------------------------------------------
    # METHOD: list_pins
    # -------------------------------------------------------------------------

    async def list_pins(
        self,
        *,
        collection_id: str | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> list[Pin]:
        """
        List the documents pinned to a collection, or to the home screen.

        Returns:
            list[Pin]: The pins.
        """
        return await self._run(
            pin_ops.list_pins(collection_id=collection_id, offset=offset, limit=limit)
        )

    # -------------------------------------------------------------------------
    # METHOD: get_pin
    # -------------------------------------------------------------------------

    async def get_pin(
        self, document_id: str, *, collection_id: str | None = None
    ) -> Pin:
        """
        Retrieve the pin for one document.

        Returns:
            Pin: The pin.
        """
        return await self._run(
            pin_ops.get_pin(document_id, collection_id=collection_id)
        )

    # -------------------------------------------------------------------------
    # METHOD: create_pin
    # -------------------------------------------------------------------------

    async def create_pin(
        self,
        document_id: str,
        *,
        collection_id: str | None = None,
        index: str | None = None,
    ) -> Pin:
        """
        Pin a document, for everyone in the workspace.

        Passing `collection_id` pins it to the top of that collection;
        omitting it pins the document to the workspace home screen.

        Returns:
            Pin: The created pin.
        """
        return await self._run(
            pin_ops.create_pin(document_id, collection_id=collection_id, index=index)
        )

    # -------------------------------------------------------------------------
    # METHOD: update_pin
    # -------------------------------------------------------------------------

    async def update_pin(self, id: str, index: str) -> Pin:
        """
        Reorder a pin.

        Returns:
            Pin: The updated pin.
        """
        return await self._run(pin_ops.update_pin(id, index))

    # -------------------------------------------------------------------------
    # METHOD: delete_pin
    # -------------------------------------------------------------------------

    async def delete_pin(self, id: str) -> bool:
        """
        Unpin a document.

        Returns:
            bool: Whether the call succeeded.
        """
        return await self._run(pin_ops.delete_pin(id))

    # =========================================================================
    # SECTION: Subscriptions and notifications
    # =========================================================================

    # -------------------------------------------------------------------------
    # METHOD: list_subscriptions
    # -------------------------------------------------------------------------

    async def list_subscriptions(
        self,
        event: str,
        *,
        document_id: str | None = None,
        collection_id: str | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> list[Subscription]:
        """
        List the calling user's subscriptions to an event.

        Returns:
            list[Subscription]: The subscriptions.
        """
        return await self._run(
            subscription_ops.list_subscriptions(
                event,
                document_id=document_id,
                collection_id=collection_id,
                offset=offset,
                limit=limit,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: get_subscription
    # -------------------------------------------------------------------------

    async def get_subscription(
        self,
        event: str,
        *,
        document_id: str | None = None,
        collection_id: str | None = None,
    ) -> Subscription:
        """
        Retrieve the calling user's subscription to one document or collection.

        Returns:
            Subscription: The subscription.
        """
        return await self._run(
            subscription_ops.get_subscription(
                event, document_id=document_id, collection_id=collection_id
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: create_subscription
    # -------------------------------------------------------------------------

    async def create_subscription(
        self,
        event: str,
        *,
        document_id: str | None = None,
        collection_id: str | None = None,
    ) -> Subscription:
        """
        Subscribe the calling user to changes on a document or collection.

        Returns:
            Subscription: The created subscription.
        """
        return await self._run(
            subscription_ops.create_subscription(
                event, document_id=document_id, collection_id=collection_id
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: delete_subscription
    # -------------------------------------------------------------------------

    async def delete_subscription(self, id: str) -> bool:
        """
        Unsubscribe from a document or collection.

        Returns:
            bool: Whether the call succeeded.
        """
        return await self._run(subscription_ops.delete_subscription(id))

    # -------------------------------------------------------------------------
    # METHOD: list_notifications
    # -------------------------------------------------------------------------

    async def list_notifications(
        self,
        *,
        event_type: str | None = None,
        archived: bool | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> list[Notification]:
        """
        List the calling user's notifications.

        Returns:
            list[Notification]: The notifications.
        """
        return await self._run(
            notification_ops.list_notifications(
                event_type=event_type,
                archived=archived,
                offset=offset,
                limit=limit,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: update_notification
    # -------------------------------------------------------------------------

    async def update_notification(
        self,
        id: str,
        *,
        viewed_at: datetime | str | None = None,
        archived_at: datetime | str | None = None,
    ) -> Notification:
        """
        Mark one notification as read or archived.

        Returns:
            Notification: The updated notification.
        """
        return await self._run(
            notification_ops.update_notification(
                id, viewed_at=viewed_at, archived_at=archived_at
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: update_all_notifications
    # -------------------------------------------------------------------------

    async def update_all_notifications(
        self,
        *,
        viewed_at: datetime | str | None = None,
        archived_at: datetime | str | None = None,
    ) -> bool:
        """
        Mark every one of the calling user's notifications read or archived.

        Returns:
            bool: Whether the call succeeded.
        """
        return await self._run(
            notification_ops.update_all_notifications(
                viewed_at=viewed_at, archived_at=archived_at
            )
        )

    # =========================================================================
    # SECTION: Attachments and file operations
    # =========================================================================

    # -------------------------------------------------------------------------
    # METHOD: list_attachments
    # -------------------------------------------------------------------------

    async def list_attachments(
        self,
        *,
        document_id: str | None = None,
        user_id: str | None = None,
        offset: int | None = None,
        limit: int | None = None,
        sort: str | None = None,
        direction: SortDirection | str | None = None,
    ) -> list[Attachment]:
        """
        List the attachments the calling user can see.

        Returns:
            list[Attachment]: The matching attachments.
        """
        return await self._run(
            attachment_ops.list_attachments(
                document_id=document_id,
                user_id=user_id,
                offset=offset,
                limit=limit,
                sort=sort,
                direction=direction,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: create_attachment
    # -------------------------------------------------------------------------

    async def create_attachment(
        self,
        name: str,
        content_type: str,
        size: int,
        *,
        document_id: str | None = None,
    ) -> AttachmentUpload:
        """
        Reserve an attachment and get a pre-authorized slot to upload it to.

        This creates the record only. The returned `AttachmentUpload` says
        where and how to send the bytes, which the caller does itself - the
        upload goes to object storage, not to Outline.

        Returns:
            AttachmentUpload: The attachment record and its upload slot.
        """
        return await self._run(
            attachment_ops.create_attachment(
                name, content_type, size, document_id=document_id
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: create_attachment_from_url
    # -------------------------------------------------------------------------

    async def create_attachment_from_url(
        self,
        url: str,
        *,
        document_id: str | None = None,
        id: str | None = None,
    ) -> Attachment:
        """
        Create an attachment by having Outline fetch a URL itself.

        Returns:
            Attachment: The created attachment.
        """
        return await self._run(
            attachment_ops.create_attachment_from_url(
                url, document_id=document_id, id=id
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: delete_attachment
    # -------------------------------------------------------------------------

    async def delete_attachment(self, id: str) -> bool:
        """
        Delete an attachment and the file behind it.

        Returns:
            bool: Whether the call succeeded.
        """
        return await self._run(attachment_ops.delete_attachment(id))

    # -------------------------------------------------------------------------
    # METHOD: get_attachment_url
    # -------------------------------------------------------------------------

    async def get_attachment_url(self, id: str) -> str:
        """
        Resolve an attachment to a URL its bytes can be fetched from.

        Outline answers this method with a redirect rather than a body, and
        for a private attachment the target is a short-lived signed URL. The
        redirect is read rather than followed, so the URL can be handed to
        something else - a browser, a report, another service - without this
        client downloading the file.

        Returns:
            str: The URL the attachment is readable at.
        """
        url = self._endpoint("attachments.redirect")
        logger.info("POST %s", url)

        response = await self._http.post(
            url=url,
            json=body(id=id),
            headers=self._headers(),
            timeout=self._request_timeout(),
            follow_redirects=False,
        )
        if response.is_redirect:
            return str(response.headers["Location"])
        if not response.is_success:
            self._raise_for_status(response)

        # A storage backend that streams the file inline answers 200 with the
        # bytes instead of redirecting, in which case the method's own URL is
        # the only address the attachment has.
        return url

    # -------------------------------------------------------------------------
    # METHOD: download_attachment
    # -------------------------------------------------------------------------

    async def download_attachment(self, id: str) -> bytes:
        """
        Download an attachment's contents.

        Returns:
            bytes: The attachment's contents.
        """
        return await self._download(
            "attachments.redirect", body(id=id), "application/octet-stream"
        )

    # -------------------------------------------------------------------------
    # METHOD: list_file_operations
    # -------------------------------------------------------------------------

    async def list_file_operations(
        self,
        type: FileOperationType | str,
        *,
        offset: int | None = None,
        limit: int | None = None,
        sort: str | None = None,
        direction: SortDirection | str | None = None,
    ) -> list[FileOperation]:
        """
        List the workspace's imports or exports.

        Returns:
            list[FileOperation]: The matching file operations.
        """
        return await self._run(
            file_operation_ops.list_file_operations(
                type, offset=offset, limit=limit, sort=sort, direction=direction
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: get_file_operation
    # -------------------------------------------------------------------------

    async def get_file_operation(self, id: str) -> FileOperation:
        """
        Retrieve one file operation, to check how far it has got.

        Returns:
            FileOperation: The file operation, with its current state.
        """
        return await self._run(file_operation_ops.get_file_operation(id))

    # -------------------------------------------------------------------------
    # METHOD: download_file_operation
    # -------------------------------------------------------------------------

    async def download_file_operation(self, id: str) -> bytes:
        """
        Download the archive a completed export produced.

        Returns:
            bytes: The exported file.
        """
        return await self._download(
            "fileOperations.redirect", body(id=id), "application/octet-stream"
        )

    # -------------------------------------------------------------------------
    # METHOD: delete_file_operation
    # -------------------------------------------------------------------------

    async def delete_file_operation(self, id: str) -> bool:
        """
        Delete a file operation and the file it produced.

        Returns:
            bool: Whether the call succeeded.
        """
        return await self._run(file_operation_ops.delete_file_operation(id))

    # =========================================================================
    # SECTION: Data attributes
    # =========================================================================

    # -------------------------------------------------------------------------
    # METHOD: list_data_attributes
    # -------------------------------------------------------------------------

    async def list_data_attributes(
        self,
        *,
        offset: int | None = None,
        limit: int | None = None,
        sort: str | None = None,
        direction: SortDirection | str | None = None,
    ) -> list[DataAttribute]:
        """
        List the workspace's custom document attributes.

        Returns:
            list[DataAttribute]: The data attributes.
        """
        return await self._run(
            data_attribute_ops.list_data_attributes(
                offset=offset, limit=limit, sort=sort, direction=direction
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: get_data_attribute
    # -------------------------------------------------------------------------

    async def get_data_attribute(self, id: str) -> DataAttribute:
        """
        Retrieve one data attribute.

        Returns:
            DataAttribute: The data attribute.
        """
        return await self._run(data_attribute_ops.get_data_attribute(id))

    # -------------------------------------------------------------------------
    # METHOD: create_data_attribute
    # -------------------------------------------------------------------------

    async def create_data_attribute(
        self,
        name: str,
        data_type: DataAttributeDataType | str,
        *,
        description: str | None = None,
        options: DataAttributeOptions | None = None,
        pinned: bool | None = None,
    ) -> DataAttribute:
        """
        Define a custom attribute that documents can carry a value for.

        Args:
            name: The attribute's name.
            data_type: `string`, `number`, `boolean`, or `list`.
            description: What the attribute records.
            options: Extra configuration, including the permitted values when
                `data_type` is `list`.
            pinned: Whether to show it on documents that have no value for it.

        Returns:
            DataAttribute: The created data attribute.
        """
        return await self._run(
            data_attribute_ops.create_data_attribute(
                name,
                data_type,
                description=description,
                options=options,
                pinned=pinned,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: update_data_attribute
    # -------------------------------------------------------------------------

    async def update_data_attribute(
        self,
        id: str,
        name: str,
        *,
        description: str | None = None,
        options: DataAttributeOptions | None = None,
        pinned: bool | None = None,
    ) -> DataAttribute:
        """
        Update a data attribute.

        Returns:
            DataAttribute: The updated data attribute.
        """
        return await self._run(
            data_attribute_ops.update_data_attribute(
                id,
                name,
                description=description,
                options=options,
                pinned=pinned,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: delete_data_attribute
    # -------------------------------------------------------------------------

    async def delete_data_attribute(self, id: str) -> bool:
        """
        Delete a data attribute and every document's value for it.

        Returns:
            bool: Whether the call succeeded.
        """
        return await self._run(data_attribute_ops.delete_data_attribute(id))

    # =========================================================================
    # SECTION: Access requests
    # =========================================================================

    # -------------------------------------------------------------------------
    # METHOD: get_access_request
    # -------------------------------------------------------------------------

    async def get_access_request(
        self,
        id: str | None = None,
        *,
        document_id: str | None = None,
    ) -> AccessRequest:
        """
        Retrieve an access request, by its own id or by the document it is for.

        Returns:
            AccessRequest: The access request.
        """
        return await self._run(
            access_request_ops.get_access_request(id, document_id=document_id)
        )

    # -------------------------------------------------------------------------
    # METHOD: create_access_request
    # -------------------------------------------------------------------------

    async def create_access_request(self, document_id: str) -> AccessRequest:
        """
        Ask for access to a document the calling user cannot read.

        Returns:
            AccessRequest: The created access request.
        """
        return await self._run(access_request_ops.create_access_request(document_id))

    # -------------------------------------------------------------------------
    # METHOD: approve_access_request
    # -------------------------------------------------------------------------

    async def approve_access_request(
        self,
        id: str,
        *,
        permission: Permission | str | None = None,
    ) -> AccessRequest:
        """
        Approve an access request, granting the requester the permission.

        Returns:
            AccessRequest: The approved access request.
        """
        return await self._run(
            access_request_ops.approve_access_request(id, permission=permission)
        )

    # -------------------------------------------------------------------------
    # METHOD: dismiss_access_request
    # -------------------------------------------------------------------------

    async def dismiss_access_request(self, id: str) -> AccessRequest:
        """
        Dismiss an access request without granting it.

        Returns:
            AccessRequest: The dismissed access request.
        """
        return await self._run(access_request_ops.dismiss_access_request(id))

    # =========================================================================
    # SECTION: API keys
    # =========================================================================

    # -------------------------------------------------------------------------
    # METHOD: list_api_keys
    # -------------------------------------------------------------------------

    async def list_api_keys(
        self,
        *,
        user_id: str | None = None,
        query: str | None = None,
        offset: int | None = None,
        limit: int | None = None,
        sort: str | None = None,
        direction: SortDirection | str | None = None,
    ) -> list[ApiKey]:
        """
        List API keys the calling user can see.

        The key itself is never returned again after creation; the records
        here carry only the name, scope, and last four characters.

        Returns:
            list[ApiKey]: The matching API keys.
        """
        return await self._run(
            api_key_ops.list_api_keys(
                user_id=user_id,
                query=query,
                offset=offset,
                limit=limit,
                sort=sort,
                direction=direction,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: create_api_key
    # -------------------------------------------------------------------------

    async def create_api_key(
        self,
        name: str,
        *,
        expires_at: datetime | str | None = None,
        scope: list[str] | None = None,
    ) -> ApiKey:
        """
        Create an API key.

        The response is the only time the key's value is returned; store it
        when you get it or create another.

        Args:
            name: A label for the key.
            expires_at: When the key stops working. Omitting it creates a key
                that never expires.
            scope: What the key may reach, e.g. `["documents:read"]`. Omitting
                it creates a key with the calling user's full access.

        Returns:
            ApiKey: The created key, including its secret value.
        """
        return await self._run(
            api_key_ops.create_api_key(name, expires_at=expires_at, scope=scope)
        )

    # -------------------------------------------------------------------------
    # METHOD: delete_api_key
    # -------------------------------------------------------------------------

    async def delete_api_key(self, id: str) -> bool:
        """
        Revoke an API key.

        Returns:
            bool: Whether the call succeeded.
        """
        return await self._run(api_key_ops.delete_api_key(id))

    # =========================================================================
    # SECTION: OAuth applications
    # =========================================================================

    # -------------------------------------------------------------------------
    # METHOD: list_oauth_clients
    # -------------------------------------------------------------------------

    async def list_oauth_clients(
        self,
        *,
        offset: int | None = None,
        limit: int | None = None,
    ) -> list[OAuthClient]:
        """
        List the OAuth applications registered in the workspace.

        Returns:
            list[OAuthClient]: The OAuth clients.
        """
        return await self._run(oauth_ops.list_oauth_clients(offset=offset, limit=limit))

    # -------------------------------------------------------------------------
    # METHOD: get_oauth_client
    # -------------------------------------------------------------------------

    async def get_oauth_client(
        self,
        id: str | None = None,
        *,
        client_id: str | None = None,
    ) -> OAuthClient:
        """
        Retrieve one OAuth application, by record id or by OAuth client id.

        Returns:
            OAuthClient: The OAuth client.
        """
        return await self._run(oauth_ops.get_oauth_client(id, client_id=client_id))

    # -------------------------------------------------------------------------
    # METHOD: create_oauth_client
    # -------------------------------------------------------------------------

    async def create_oauth_client(
        self,
        name: str,
        redirect_uris: list[str],
        *,
        description: str | None = None,
        developer_name: str | None = None,
        developer_url: str | None = None,
        avatar_url: str | None = None,
        published: bool | None = None,
    ) -> OAuthClient:
        """
        Register an OAuth application.

        The response is the only time the client secret is returned in full.

        Returns:
            OAuthClient: The created client, including its secret.
        """
        return await self._run(
            oauth_ops.create_oauth_client(
                name,
                redirect_uris,
                description=description,
                developer_name=developer_name,
                developer_url=developer_url,
                avatar_url=avatar_url,
                published=published,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: update_oauth_client
    # -------------------------------------------------------------------------

    async def update_oauth_client(
        self,
        id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        developer_name: str | None = None,
        developer_url: str | None = None,
        avatar_url: str | None = None,
        redirect_uris: list[str] | None = None,
        published: bool | None = None,
    ) -> OAuthClient:
        """
        Update an OAuth application.

        Returns:
            OAuthClient: The updated client.
        """
        return await self._run(
            oauth_ops.update_oauth_client(
                id,
                name=name,
                description=description,
                developer_name=developer_name,
                developer_url=developer_url,
                avatar_url=avatar_url,
                redirect_uris=redirect_uris,
                published=published,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: rotate_oauth_client_secret
    # -------------------------------------------------------------------------

    async def rotate_oauth_client_secret(self, id: str) -> OAuthClient:
        """
        Issue a new secret for an OAuth application, invalidating the old one.

        Returns:
            OAuthClient: The client, including its new secret.
        """
        return await self._run(oauth_ops.rotate_oauth_client_secret(id))

    # -------------------------------------------------------------------------
    # METHOD: delete_oauth_client
    # -------------------------------------------------------------------------

    async def delete_oauth_client(self, id: str) -> bool:
        """
        Delete an OAuth application and revoke the grants it holds.

        Returns:
            bool: Whether the call succeeded.
        """
        return await self._run(oauth_ops.delete_oauth_client(id))

    # -------------------------------------------------------------------------
    # METHOD: list_oauth_authentications
    # -------------------------------------------------------------------------

    async def list_oauth_authentications(
        self,
        *,
        offset: int | None = None,
        limit: int | None = None,
    ) -> list[OAuthAuthentication]:
        """
        List the OAuth applications the calling user has authorized.

        Returns:
            list[OAuthAuthentication]: The authorizations.
        """
        return await self._run(
            oauth_ops.list_oauth_authentications(offset=offset, limit=limit)
        )

    # -------------------------------------------------------------------------
    # METHOD: delete_oauth_authentication
    # -------------------------------------------------------------------------

    async def delete_oauth_authentication(
        self,
        oauth_client_id: str,
        *,
        scope: list[str] | None = None,
    ) -> bool:
        """
        Revoke an OAuth application's access, in whole or by scope.

        Returns:
            bool: Whether the call succeeded.
        """
        return await self._run(
            oauth_ops.delete_oauth_authentication(oauth_client_id, scope=scope)
        )

    # =========================================================================
    # SECTION: Webhooks, events, and views
    # =========================================================================

    # -------------------------------------------------------------------------
    # METHOD: list_webhook_subscriptions
    # -------------------------------------------------------------------------

    async def list_webhook_subscriptions(
        self,
        *,
        query: str | None = None,
        offset: int | None = None,
        limit: int | None = None,
        sort: str | None = None,
        direction: SortDirection | str | None = None,
    ) -> list[WebhookSubscription]:
        """
        List the workspace's webhook subscriptions.

        Returns:
            list[WebhookSubscription]: The matching subscriptions.
        """
        return await self._run(
            webhook_ops.list_webhook_subscriptions(
                query=query,
                offset=offset,
                limit=limit,
                sort=sort,
                direction=direction,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: create_webhook_subscription
    # -------------------------------------------------------------------------

    async def create_webhook_subscription(
        self,
        name: str,
        url: str,
        events: list[str],
        *,
        secret: str | None = None,
    ) -> WebhookSubscription:
        """
        Subscribe a URL to workspace events.

        Args:
            name: A label for the subscription.
            url: Where the events are delivered.
            events: The event names to deliver, e.g. `["documents.update"]`.
                `["*"]` subscribes to everything.
            secret: A signing secret, used to prove a delivery came from
                Outline.

        Returns:
            WebhookSubscription: The created subscription.
        """
        return await self._run(
            webhook_ops.create_webhook_subscription(name, url, events, secret=secret)
        )

    # -------------------------------------------------------------------------
    # METHOD: update_webhook_subscription
    # -------------------------------------------------------------------------

    async def update_webhook_subscription(
        self,
        id: str,
        name: str,
        url: str,
        events: list[str],
        *,
        secret: str | None = None,
    ) -> WebhookSubscription:
        """
        Update a webhook subscription.

        Outline requires the full set of fields here, so this replaces the
        subscription rather than patching it.

        Returns:
            WebhookSubscription: The updated subscription.
        """
        return await self._run(
            webhook_ops.update_webhook_subscription(
                id, name, url, events, secret=secret
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: delete_webhook_subscription
    # -------------------------------------------------------------------------

    async def delete_webhook_subscription(self, id: str) -> bool:
        """
        Delete a webhook subscription.

        Returns:
            bool: Whether the call succeeded.
        """
        return await self._run(webhook_ops.delete_webhook_subscription(id))

    # -------------------------------------------------------------------------
    # METHOD: list_events
    # -------------------------------------------------------------------------

    async def list_events(
        self,
        *,
        name: str | None = None,
        actor_id: str | None = None,
        document_id: str | None = None,
        collection_id: str | None = None,
        audit_log: bool | None = None,
        offset: int | None = None,
        limit: int | None = None,
        sort: str | None = None,
        direction: SortDirection | str | None = None,
    ) -> list[Event]:
        """
        List what has happened in the workspace.

        Args:
            name: Limit to one event name, e.g. `documents.update`.
            actor_id: Limit to events caused by one user.
            document_id: Limit to events about one document.
            collection_id: Limit to events about one collection.
            audit_log: Include the administrative events that make up the
                audit log, which requires an admin token.
            offset: How many records to skip.
            limit: How many records to return.
            sort: Field to order by.
            direction: `ASC` or `DESC`.

        Returns:
            list[Event]: The matching events.
        """
        return await self._run(
            event_ops.list_events(
                name=name,
                actor_id=actor_id,
                document_id=document_id,
                collection_id=collection_id,
                audit_log=audit_log,
                offset=offset,
                limit=limit,
                sort=sort,
                direction=direction,
            )
        )

    # -------------------------------------------------------------------------
    # METHOD: list_views
    # -------------------------------------------------------------------------

    async def list_views(
        self,
        document_id: str,
        *,
        include_suspended: bool | None = None,
    ) -> list[View]:
        """
        List who has read a document, and how often.

        Returns:
            list[View]: One record per user who has viewed the document.
        """
        return await self._run(
            view_ops.list_views(document_id, include_suspended=include_suspended)
        )
