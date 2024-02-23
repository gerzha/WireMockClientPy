from typing import Any, Self

from qawiremock import Stub, WiremockClient
from qawiremock.models import WireMockRequest, WireMockResponse


class StubContextManager:
    def __init__(
        self,
        mock_client: WiremockClient,
    ) -> None:
        self.mock_client: WiremockClient = mock_client
        self.stubs: list[Stub] = []

    def create_stub(
        self, stub_request: WireMockRequest, stub_response: WireMockResponse
    ) -> None:
        """Creates and registers a stub within the context manager."""
        stub = Stub().when(stub_request).reply(stub_response)
        self.mock_client.create_stub(stub)
        self.stubs.append(stub)

    def __enter__(self) -> Self:
        """Return self to allow creation of stubs within the context."""
        return self

    def __exit__(
        self, exc_type: type | None, exc_val: Exception | None, exc_tb: Any | None
    ) -> None:
        """Ensure all created stubs are deleted on exiting the context."""
        for stub in self.stubs:
            self.mock_client.delete_stub(stub=stub)
        self.stubs.clear()
