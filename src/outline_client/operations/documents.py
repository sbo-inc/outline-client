from datetime import date, datetime

from outline_client.operations.generic import (
    Operation,
    body,
    many,
    one,
    success,
    whole,
)
from outline_client.operations.generic import (
    text as text_result,
)
from outline_client.schemas.models import (
    Document,
    DocumentDataAttribute,
    DocumentFilterCondition,
    DocumentFilterGroup,
    DocumentInsight,
    DocumentPreferences,
    DocumentsDeletedFilterCondition,
    DocumentsDeletedFilterGroup,
    NavigationNode,
    Permission,
    SortDirection,
    Template,
    TextEditMode,
    User,
)
from outline_client.schemas.results import (
    AnswerResult,
    DocumentGroupMembershipsResult,
    DocumentMoveResult,
    DocumentsResult,
    MembershipsResult,
    SearchHit,
)

# The filter expression accepted by `documents.list` and the search methods: a
# leaf condition or a nested `AND`/`OR` group, evaluated as an AND of the
# top-level entries.
type DocumentFilters = list[DocumentFilterCondition | DocumentFilterGroup]

# The equivalent for `documents.deleted`, whose fields are restricted to the
# ones a deleted document has.
type DeletedFilters = list[
    DocumentsDeletedFilterCondition | DocumentsDeletedFilterGroup
]

# -----------------------------------------------------------------------------
# OPERATION: list_documents
# -----------------------------------------------------------------------------


def list_documents(
    *,
    filters: DocumentFilters | None = None,
    backlink_document_id: str | None = None,
    collection_id: str | None = None,
    user_id: str | None = None,
    parent_document_id: str | None = None,
    status_filter: list[str] | None = None,
    offset: int | None = None,
    limit: int | None = None,
    sort: str | None = None,
    direction: SortDirection | str | None = None,
) -> Operation[list[Document]]:
    """
    Build the `documents.list` operation.

    Returns:
        Operation[list[Document]]: The list documents operation.
    """
    return Operation(
        path="documents.list",
        payload=body(
            filters=filters,
            backlinkDocumentId=backlink_document_id,
            collectionId=collection_id,
            userId=user_id,
            parentDocumentId=parent_document_id,
            statusFilter=status_filter,
            offset=offset,
            limit=limit,
            sort=sort,
            direction=direction,
        ),
        parse=many(Document),
    )


# -----------------------------------------------------------------------------
# OPERATION: get_document
# -----------------------------------------------------------------------------


def get_document(
    id: str | None = None,
    *,
    share_id: str | None = None,
) -> Operation[Document]:
    """
    Build the `documents.info` operation.

    Returns:
        Operation[Document]: The get document operation.
    """
    return Operation(
        path="documents.info",
        payload=body(id=id, shareId=share_id),
        parse=one(Document),
    )


# -----------------------------------------------------------------------------
# OPERATION: get_document_structure
# -----------------------------------------------------------------------------


def get_document_structure(id: str) -> Operation[NavigationNode]:
    """
    Build the `documents.documents` operation.

    Returns:
        Operation[NavigationNode]: The get document structure operation.
    """
    return Operation(
        path="documents.documents",
        payload=body(id=id),
        parse=one(NavigationNode),
    )


# -----------------------------------------------------------------------------
# OPERATION: create_document
# -----------------------------------------------------------------------------


def create_document(
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
) -> Operation[Document]:
    """
    Build the `documents.create` operation.

    Returns:
        Operation[Document]: The create document operation.
    """
    return Operation(
        path="documents.create",
        payload=body(
            id=id,
            title=title,
            text=text,
            icon=icon,
            color=color,
            collectionId=collection_id,
            parentDocumentId=parent_document_id,
            templateId=template_id,
            publish=publish,
            fullWidth=full_width,
            preferences=preferences,
            createdAt=created_at,
            dataAttributes=data_attributes,
        ),
        parse=one(Document),
    )


# -----------------------------------------------------------------------------
# OPERATION: update_document
# -----------------------------------------------------------------------------


def update_document(
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
) -> Operation[Document]:
    """
    Build the `documents.update` operation.

    Returns:
        Operation[Document]: The update document operation.
    """
    return Operation(
        path="documents.update",
        payload=body(
            id=id,
            title=title,
            text=text,
            icon=icon,
            color=color,
            fullWidth=full_width,
            preferences=preferences,
            templateId=template_id,
            collectionId=collection_id,
            insightsEnabled=insights_enabled,
            editMode=edit_mode,
            findText=find_text,
            publish=publish,
            lastRevision=last_revision,
            dataAttributes=data_attributes,
        ),
        parse=one(Document),
    )


# -----------------------------------------------------------------------------
# OPERATION: delete_document
# -----------------------------------------------------------------------------


def delete_document(
    id: str,
    *,
    permanent: bool | None = None,
) -> Operation[bool]:
    """
    Build the `documents.delete` operation.

    Returns:
        Operation[bool]: The delete document operation.
    """
    return Operation(
        path="documents.delete",
        payload=body(id=id, permanent=permanent),
        parse=success,
    )


# -----------------------------------------------------------------------------
# OPERATION: move_document
# -----------------------------------------------------------------------------


def move_document(
    id: str,
    *,
    collection_id: str | None = None,
    parent_document_id: str | None = None,
    index: float | None = None,
) -> Operation[DocumentMoveResult]:
    """
    Build the `documents.move` operation.

    Returns:
        Operation[DocumentMoveResult]: The move document operation.
    """
    return Operation(
        path="documents.move",
        payload=body(
            id=id,
            collectionId=collection_id,
            parentDocumentId=parent_document_id,
            index=index,
        ),
        parse=one(DocumentMoveResult),
    )


# -----------------------------------------------------------------------------
# OPERATION: duplicate_document
# -----------------------------------------------------------------------------


def duplicate_document(
    id: str,
    *,
    title: str | None = None,
    recursive: bool | None = None,
    publish: bool | None = None,
    collection_id: str | None = None,
    parent_document_id: str | None = None,
) -> Operation[DocumentsResult]:
    """
    Build the `documents.duplicate` operation.

    Returns:
        Operation[DocumentsResult]: The duplicate document operation.
    """
    return Operation(
        path="documents.duplicate",
        payload=body(
            id=id,
            title=title,
            recursive=recursive,
            publish=publish,
            collectionId=collection_id,
            parentDocumentId=parent_document_id,
        ),
        parse=one(DocumentsResult),
    )


# -----------------------------------------------------------------------------
# OPERATION: archive_document
# -----------------------------------------------------------------------------


def archive_document(id: str) -> Operation[Document]:
    """
    Build the `documents.archive` operation.

    Returns:
        Operation[Document]: The archive document operation.
    """
    return Operation(
        path="documents.archive",
        payload=body(id=id),
        parse=one(Document),
    )


# -----------------------------------------------------------------------------
# OPERATION: restore_document
# -----------------------------------------------------------------------------


def restore_document(
    id: str,
    *,
    collection_id: str | None = None,
    revision_id: str | None = None,
) -> Operation[Document]:
    """
    Build the `documents.restore` operation.

    Returns:
        Operation[Document]: The restore document operation.
    """
    return Operation(
        path="documents.restore",
        payload=body(id=id, collectionId=collection_id, revisionId=revision_id),
        parse=one(Document),
    )


# -----------------------------------------------------------------------------
# OPERATION: unpublish_document
# -----------------------------------------------------------------------------


def unpublish_document(
    id: str,
    *,
    detach: bool | None = None,
) -> Operation[Document]:
    """
    Build the `documents.unpublish` operation.

    Returns:
        Operation[Document]: The unpublish document operation.
    """
    return Operation(
        path="documents.unpublish",
        payload=body(id=id, detach=detach),
        parse=one(Document),
    )


# -----------------------------------------------------------------------------
# OPERATION: templatize_document
# -----------------------------------------------------------------------------


def templatize_document(
    id: str,
    publish: bool,
    *,
    collection_id: str | None = None,
) -> Operation[Template]:
    """
    Build the `documents.templatize` operation.

    Returns:
        Operation[Template]: The templatize document operation.
    """
    return Operation(
        path="documents.templatize",
        payload=body(id=id, publish=publish, collectionId=collection_id),
        parse=one(Template),
    )


# -----------------------------------------------------------------------------
# OPERATION: empty_trash
# -----------------------------------------------------------------------------


def empty_trash() -> Operation[bool]:
    """
    Build the `documents.empty_trash` operation.

    Returns:
        Operation[bool]: The empty trash operation.
    """
    return Operation(
        path="documents.empty_trash",
        payload=body(),
        parse=success,
    )


# -----------------------------------------------------------------------------
# OPERATION: list_archived_documents
# -----------------------------------------------------------------------------


def list_archived_documents(
    *,
    collection_id: str | None = None,
    offset: int | None = None,
    limit: int | None = None,
    sort: str | None = None,
    direction: SortDirection | str | None = None,
) -> Operation[list[Document]]:
    """
    Build the `documents.archived` operation.

    Returns:
        Operation[list[Document]]: The list archived documents operation.
    """
    return Operation(
        path="documents.archived",
        payload=body(
            collectionId=collection_id,
            offset=offset,
            limit=limit,
            sort=sort,
            direction=direction,
        ),
        parse=many(Document),
    )


# -----------------------------------------------------------------------------
# OPERATION: list_deleted_documents
# -----------------------------------------------------------------------------


def list_deleted_documents(
    *,
    filters: DeletedFilters | None = None,
    offset: int | None = None,
    limit: int | None = None,
    sort: str | None = None,
    direction: SortDirection | str | None = None,
) -> Operation[list[Document]]:
    """
    Build the `documents.deleted` operation.

    Returns:
        Operation[list[Document]]: The list deleted documents operation.
    """
    return Operation(
        path="documents.deleted",
        payload=body(
            filters=filters,
            offset=offset,
            limit=limit,
            sort=sort,
            direction=direction,
        ),
        parse=many(Document),
    )


# -----------------------------------------------------------------------------
# OPERATION: list_draft_documents
# -----------------------------------------------------------------------------


def list_draft_documents(
    *,
    collection_id: str | None = None,
    date_filter: str | None = None,
    offset: int | None = None,
    limit: int | None = None,
    sort: str | None = None,
    direction: SortDirection | str | None = None,
) -> Operation[list[Document]]:
    """
    Build the `documents.drafts` operation.

    Returns:
        Operation[list[Document]]: The list draft documents operation.
    """
    return Operation(
        path="documents.drafts",
        payload=body(
            collectionId=collection_id,
            dateFilter=date_filter,
            offset=offset,
            limit=limit,
            sort=sort,
            direction=direction,
        ),
        parse=many(Document),
    )


# -----------------------------------------------------------------------------
# OPERATION: list_viewed_documents
# -----------------------------------------------------------------------------


def list_viewed_documents(
    *,
    offset: int | None = None,
    limit: int | None = None,
    sort: str | None = None,
    direction: SortDirection | str | None = None,
) -> Operation[list[Document]]:
    """
    Build the `documents.viewed` operation.

    Returns:
        Operation[list[Document]]: The list viewed documents operation.
    """
    return Operation(
        path="documents.viewed",
        payload=body(offset=offset, limit=limit, sort=sort, direction=direction),
        parse=many(Document),
    )


# -----------------------------------------------------------------------------
# OPERATION: search_documents
# -----------------------------------------------------------------------------


def search_documents(
    query: str | None = None,
    *,
    filters: DocumentFilters | None = None,
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
) -> Operation[list[SearchHit]]:
    """
    Build the `documents.search` operation.

    Returns:
        Operation[list[SearchHit]]: The search documents operation.
    """
    return Operation(
        path="documents.search",
        payload=body(
            query=query,
            filters=filters,
            collectionId=collection_id,
            documentId=document_id,
            userId=user_id,
            statusFilter=status_filter,
            dateFilter=date_filter,
            shareId=share_id,
            snippetMinWords=snippet_min_words,
            snippetMaxWords=snippet_max_words,
            offset=offset,
            limit=limit,
            sort=sort,
            direction=direction,
        ),
        parse=many(SearchHit),
    )


# -----------------------------------------------------------------------------
# OPERATION: search_document_titles
# -----------------------------------------------------------------------------


def search_document_titles(
    query: str,
    *,
    filters: DocumentFilters | None = None,
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
) -> Operation[list[Document]]:
    """
    Build the `documents.search_titles` operation.

    Returns:
        Operation[list[Document]]: The search document titles operation.
    """
    return Operation(
        path="documents.search_titles",
        payload=body(
            query=query,
            filters=filters,
            collectionId=collection_id,
            documentId=document_id,
            userId=user_id,
            statusFilter=status_filter,
            dateFilter=date_filter,
            shareId=share_id,
            offset=offset,
            limit=limit,
            sort=sort,
            direction=direction,
        ),
        parse=many(Document),
    )


# -----------------------------------------------------------------------------
# OPERATION: answer_question
# -----------------------------------------------------------------------------


def answer_question(
    query: str,
    *,
    collection_id: str | None = None,
    document_id: str | None = None,
    user_id: str | None = None,
    status_filter: str | None = None,
    date_filter: str | None = None,
) -> Operation[AnswerResult]:
    """
    Build the `documents.answerQuestion` operation.

    Returns:
        Operation[AnswerResult]: The answer question operation.
    """
    return Operation(
        path="documents.answerQuestion",
        payload=body(
            query=query,
            collectionId=collection_id,
            documentId=document_id,
            userId=user_id,
            statusFilter=status_filter,
            dateFilter=date_filter,
        ),
        parse=whole(AnswerResult),
    )


# -----------------------------------------------------------------------------
# OPERATION: export_document
# -----------------------------------------------------------------------------


def export_document(
    id: str,
    *,
    paper_size: str | None = None,
    signed_urls: int | None = None,
    include_child_documents: bool | None = None,
) -> Operation[str]:
    """
    Build the `documents.export` operation.

    Returns:
        Operation[str]: The export document operation.
    """
    return Operation(
        path="documents.export",
        payload=body(
            id=id,
            paperSize=paper_size,
            signedUrls=signed_urls,
            includeChildDocuments=include_child_documents,
        ),
        parse=text_result,
    )


# -----------------------------------------------------------------------------
# OPERATION: list_document_insights
# -----------------------------------------------------------------------------


def list_document_insights(
    id: str,
    *,
    start_date: date | str | None = None,
    end_date: date | str | None = None,
) -> Operation[list[DocumentInsight]]:
    """
    Build the `documents.insights` operation.

    Returns:
        Operation[list[DocumentInsight]]: The list document insights operation.
    """
    return Operation(
        path="documents.insights",
        payload=body(id=id, startDate=start_date, endDate=end_date),
        parse=many(DocumentInsight),
    )


# -----------------------------------------------------------------------------
# OPERATION: list_document_users
# -----------------------------------------------------------------------------


def list_document_users(
    id: str,
    *,
    query: str | None = None,
    user_id: str | None = None,
) -> Operation[list[User]]:
    """
    Build the `documents.users` operation.

    Returns:
        Operation[list[User]]: The list document users operation.
    """
    return Operation(
        path="documents.users",
        payload=body(id=id, query=query, userId=user_id),
        parse=many(User),
    )


# -----------------------------------------------------------------------------
# OPERATION: list_document_memberships
# -----------------------------------------------------------------------------


def list_document_memberships(
    id: str,
    *,
    query: str | None = None,
    permission: Permission | str | None = None,
) -> Operation[MembershipsResult]:
    """
    Build the `documents.memberships` operation.

    Returns:
        Operation[MembershipsResult]: The list document memberships operation.
    """
    return Operation(
        path="documents.memberships",
        payload=body(id=id, query=query, permission=permission),
        parse=one(MembershipsResult),
    )


# -----------------------------------------------------------------------------
# OPERATION: add_document_user
# -----------------------------------------------------------------------------


def add_document_user(
    id: str,
    user_id: str,
    *,
    permission: Permission | str | None = None,
) -> Operation[MembershipsResult]:
    """
    Build the `documents.add_user` operation.

    Returns:
        Operation[MembershipsResult]: The add document user operation.
    """
    return Operation(
        path="documents.add_user",
        payload=body(id=id, userId=user_id, permission=permission),
        parse=one(MembershipsResult),
    )


# -----------------------------------------------------------------------------
# OPERATION: remove_document_user
# -----------------------------------------------------------------------------


def remove_document_user(id: str, user_id: str) -> Operation[bool]:
    """
    Build the `documents.remove_user` operation.

    Returns:
        Operation[bool]: The remove document user operation.
    """
    return Operation(
        path="documents.remove_user",
        payload=body(id=id, userId=user_id),
        parse=success,
    )


# -----------------------------------------------------------------------------
# OPERATION: list_document_group_memberships
# -----------------------------------------------------------------------------


def list_document_group_memberships(
    id: str,
    *,
    query: str | None = None,
    permission: Permission | str | None = None,
    offset: int | None = None,
    limit: int | None = None,
) -> Operation[DocumentGroupMembershipsResult]:
    """
    Build the `documents.group_memberships` operation.

    Returns:
        Operation[DocumentGroupMembershipsResult]: The list document group
            memberships operation.
    """
    return Operation(
        path="documents.group_memberships",
        payload=body(
            id=id,
            query=query,
            permission=permission,
            offset=offset,
            limit=limit,
        ),
        parse=one(DocumentGroupMembershipsResult),
    )


# -----------------------------------------------------------------------------
# OPERATION: add_document_group
# -----------------------------------------------------------------------------


def add_document_group(
    id: str,
    group_id: str,
    *,
    permission: Permission | str | None = None,
) -> Operation[DocumentGroupMembershipsResult]:
    """
    Build the `documents.add_group` operation.

    Returns:
        Operation[DocumentGroupMembershipsResult]: The add document group operation.
    """
    return Operation(
        path="documents.add_group",
        payload=body(id=id, groupId=group_id, permission=permission),
        parse=one(DocumentGroupMembershipsResult),
    )


# -----------------------------------------------------------------------------
# OPERATION: remove_document_group
# -----------------------------------------------------------------------------


def remove_document_group(id: str, group_id: str) -> Operation[bool]:
    """
    Build the `documents.remove_group` operation.

    Returns:
        Operation[bool]: The remove document group operation.
    """
    return Operation(
        path="documents.remove_group",
        payload=body(id=id, groupId=group_id),
        parse=success,
    )


# -----------------------------------------------------------------------------
# OPERATION: import_document
# -----------------------------------------------------------------------------


def import_document(
    *,
    collection_id: str | None = None,
    parent_document_id: str | None = None,
    publish: bool | None = None,
) -> Operation[Document]:
    """
    Build the `documents.import` operation.

    The file itself is not part of the payload: this is the one method Outline
    accepts as `multipart/form-data`, so the client sends `payload` as form
    fields alongside the uploaded file rather than as a JSON body.

    Returns:
        Operation[Document]: The import document operation.
    """
    return Operation(
        path="documents.import",
        payload=body(
            collectionId=collection_id,
            parentDocumentId=parent_document_id,
            publish=publish,
        ),
        parse=one(Document),
    )
