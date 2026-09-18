"""
The result models for the composite payloads the specification leaves anonymous.
"""

from outline_client.schemas.results import (
    AttachmentUpload,
    AuthConfig,
    CollectionGroupMembershipsResult,
    FileOperationResult,
    GroupMembershipsResult,
    MembershipsResult,
    SearchHit,
    StarsResult,
)


class TestBagsDefaultToEmpty:
    def test_a_missing_member_reads_as_an_empty_list(self) -> None:
        # Outline omits a bundle member it has nothing to report for.
        result = MembershipsResult.model_validate({})

        assert result.users == []
        assert result.memberships == []

    def test_reads_the_wire_spelling_of_the_membership_arrays(self) -> None:
        result = CollectionGroupMembershipsResult.model_validate(
            {"collectionGroupMemberships": [{"permission": "read"}]}
        )

        assert len(result.collection_group_memberships) == 1

    def test_a_group_bundle_populates_only_what_the_method_returns(self) -> None:
        result = GroupMembershipsResult.model_validate(
            {"groups": [{"name": "Engineering"}], "groupMemberships": []}
        )

        assert result.groups[0].name == "Engineering"
        assert result.users == []
        assert result.documents == []


class TestAuthConfig:
    def test_reads_the_provider_list_the_server_actually_sends(self) -> None:
        # The specification calls it `services`; Outline 1.10 sends `providers`.
        config = AuthConfig.model_validate(
            {
                "name": "Example",
                "customTheme": False,
                "providers": [{"id": "oidc", "name": "SSO", "authUrl": "/auth/oidc"}],
            }
        )

        assert config.custom_theme is False
        assert config.providers[0].id == "oidc"

    def test_also_reads_the_spelling_the_specification_documents(self) -> None:
        config = AuthConfig.model_validate(
            {"name": "Example", "services": [{"id": "google", "name": "Google"}]}
        )

        assert config.providers[0].id == "google"


class TestAttachmentUpload:
    def test_describes_where_and_how_to_upload(self) -> None:
        upload = AttachmentUpload.model_validate(
            {
                "maxUploadSize": 1000,
                "mode": "post",
                "uploadUrl": "https://storage.test/upload",
                "form": {"key": "abc"},
                "attachment": {"name": "note.txt"},
            }
        )

        assert upload.mode == "post"
        assert upload.upload_url == "https://storage.test/upload"
        assert upload.form == {"key": "abc"}
        assert upload.headers == {}
        assert upload.attachment is not None
        assert upload.attachment.name == "note.txt"


class TestOtherResults:
    def test_a_file_operation_result_unwraps_the_queued_job(self) -> None:
        result = FileOperationResult.model_validate(
            {"fileOperation": {"state": "creating", "type": "export"}}
        )

        assert result.file_operation is not None
        assert result.file_operation.state == "creating"

    def test_a_search_hit_carries_the_matching_context(self) -> None:
        hit = SearchHit.model_validate(
            {
                "context": "<b>Hi</b>",
                "ranking": 0.5,
                "document": {"title": "Onboarding"},
            }
        )

        assert hit.context == "<b>Hi</b>"
        assert hit.document is not None
        assert hit.document.title == "Onboarding"

    def test_stars_come_back_with_the_documents_they_point_at(self) -> None:
        result = StarsResult.model_validate(
            {"stars": [{"index": "P"}], "documents": [{"title": "Onboarding"}]}
        )

        assert result.stars[0].index == "P"
        assert result.documents[0].title == "Onboarding"
