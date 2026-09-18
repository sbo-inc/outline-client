"""
The wrappers every response arrives in.
"""

from outline_client.schemas.envelopes import ListResponse, Response, SuccessResponse
from outline_client.schemas.models import Document


class TestResponse:
    def test_carries_the_policies_alongside_the_data(self) -> None:
        envelope = Response[Document].model_validate(
            {
                "data": {"title": "Onboarding"},
                "policies": [
                    {
                        "id": "9884b98e-3c7b-4a8a-964d-c64ce9002d21",
                        "abilities": {"read": True},
                    }
                ],
            }
        )

        assert envelope.data.title == "Onboarding"
        assert str(envelope.policies[0].id) == "9884b98e-3c7b-4a8a-964d-c64ce9002d21"

    def test_policies_default_to_empty_when_outline_sends_none(self) -> None:
        envelope = Response[Document].model_validate({"data": {"title": "Onboarding"}})

        assert envelope.policies == []


class TestListResponse:
    def test_carries_the_window_that_produced_the_page(self) -> None:
        envelope = ListResponse[Document].model_validate(
            {
                "data": [{"title": "Onboarding"}],
                "pagination": {"offset": 25, "limit": 50},
            }
        )

        assert envelope.pagination is not None
        assert envelope.pagination.offset == 25
        assert envelope.pagination.limit == 50

    def test_keeps_the_fields_outline_adds_to_pagination(self) -> None:
        # Outline sends `total` and `nextPath` beside the window; the models
        # allow extras so a caller can still reach them.
        envelope = ListResponse[Document].model_validate(
            {"data": [], "pagination": {"offset": 0, "limit": 25, "total": 100}}
        )

        assert envelope.pagination is not None
        assert envelope.pagination.__pydantic_extra__ == {"total": 100}

    def test_an_empty_page_is_an_empty_list(self) -> None:
        assert ListResponse[Document].model_validate({}).data == []


class TestSuccessResponse:
    def test_reads_the_acknowledgement(self) -> None:
        assert SuccessResponse.model_validate({"success": True}).success is True
