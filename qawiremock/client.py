import random
from copy import deepcopy
from enum import StrEnum
from typing import Any, Self

from requests import Response, delete, get, post

from qawiremock.models import (
    MappingModel,
    RequestMappingModel,
    WireMockRequest,
    WiremockRequestsHistoryModel,
    WireMockResponse,
)
from qawiremock.report import Logger


class Urls(StrEnum):
    MAPPINGS = "/__admin/mappings"
    REQUESTS = "/__admin/requests"


class Stub(Logger):
    def __init__(
        self,
        request: WireMockRequest | None = None,
        response: WireMockResponse | None = None,
    ):
        self.ids: list[str] = []
        self.request: WireMockRequest | None = request
        self.response: WireMockResponse | None = response
        self.scenario_name: str | None = None
        self.required_scenario_state: str | None = None
        self.new_scenario_state: str | None = None
        self.times: int = 0
        self.priority: int | None = None

    def when(self, request: WireMockRequest) -> Self:
        """
        Set the request for the stub.

        :param request: The Request object to set.
        :return: Self for chaining.
        """

        self.request = request
        self.attach_stub_request(self.request)
        return self

    def reply(
        self,
        response: WireMockResponse,
        times: int = 0,
        priority: int | None = None,
    ) -> Self:
        """
        Set the response for the stub, along with optional times and priority.
        :param response: The Response object to reply with.
        :param times: Number of times to reply. 0 means reply every time (default: 0).
        :param priority: The priority of the response (optional).
        :return: Self for chaining.

        if times == 0 -> reply every time
        """
        self.times = times
        self.response = response
        self.attach_stub_response(self.response)
        self.priority = priority
        return self

    def get_mapping(self) -> dict[str, Any]:
        """
        Get a dictionary representation of the stub mapping.

        :return: A dictionary representing the stub mapping.
        """
        mapping = {}

        if self.request is not None and self.response is not None:
            mapping_model = MappingModel(
                request=self.request,
                response=self.response,
            )
            mapping = mapping_model.model_dump(exclude_none=True, by_alias=True)

        if self.scenario_name:
            mapping.update(
                {
                    "scenarioName": self.scenario_name,
                    "requiredScenarioState": self.required_scenario_state,
                }
            )
            if self.new_scenario_state:
                mapping["newScenarioState"] = self.new_scenario_state
        if self.priority:
            mapping["priority"] = self.priority
        return mapping


class Scenario:
    def __init__(self, name: str | None = None):
        self.name: str = name or f"scenario_{random.randint(0, 2**63 - 1)}"
        self.scenario_stubs: list[Stub] = []

    def stub_for_state(
        self,
        stub: Stub,
        required_state: str = "Started",
        new_state: str | None = None,
    ) -> Self:
        """
        Configure a stub to respond based on a specific scenario state.

        :param stub: The Stub object to be configured.
        :param required_state: The state required for this stub to be active.
        :param new_state: The new state to transition to after this stub is used.
        :return: The Scenario object for chaining.
        """
        stub.scenario_name = self.name
        stub.required_scenario_state = required_state
        stub.new_scenario_state = new_state
        self.scenario_stubs.append(stub)
        return self

    def limited_responses_stub(self, stub: Stub, times: int = 1) -> list[Stub]:
        """
        Create a limited number of response stubs based on the provided stub.

        :param stub: The base Stub object to be replicated.
        :param times: The number of times the stub should respond (default is 1).
        :return: A list of Stub objects configured for limited responses.
        """
        for time in range(times):
            s: Stub = deepcopy(stub)
            s.scenario_name = self.name
            s.new_scenario_state = f"state_{time + 1}"
            s.required_scenario_state = "Started" if time == 0 else f"state_{time}"
            self.scenario_stubs.append(s)
        if not self.scenario_stubs:
            self.scenario_stubs.append(stub)
        return self.scenario_stubs


class WiremockClient(Logger):
    HTTP_TIMEOUT = 10

    def __init__(self, host: str, port: int = 80, timeout: int = HTTP_TIMEOUT) -> None:
        self.host: str = host
        self.port: int = port
        self.timeout: int = timeout

    def __get_base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def get_all_stubs(self) -> Any:
        """
        Retrieve all stubs from the Wiremock server.

        :return: JSON response containing all stubs.
        """
        response: Response = get(
            f"{self.__get_base_url()}{Urls.MAPPINGS}", timeout=self.timeout
        )
        self.attach_response(response)
        return response.json()

    def delete_all_stubs(self) -> Response:
        """
        Delete all stubs from the Wiremock server.

        :return: The HTTP response object.
        """
        response = delete(
            f"{self.__get_base_url()}{Urls.MAPPINGS}", timeout=self.timeout
        )
        self.attach_response(response)
        return response

    def get_stub(self, stub: Stub) -> Any:
        """
        Retrieve a specific stub by its ID from the Wiremock server.

        :param stub: The ID of the stub to retrieve.
        :return: JSON response containing the requested stub.
        """
        wrapped_response = []
        for _id in stub.ids:
            response = get(
                f"{self.__get_base_url()}{Urls.MAPPINGS}/{_id}", timeout=self.timeout
            )
            wrapped_response.append(RequestMappingModel(**response.json()))
            self.attach_response(response)
        return wrapped_response

    def create_stub(self, stub: Stub) -> Stub:
        """
        Create a specific stub in the Wiremock server.

        :param stub: The ID of the stub to retrieve.
        :return: Stub objest.
        """

        stubs: list[Stub] = Scenario().limited_responses_stub(stub, stub.times)
        if stub.times > 1:
            stub.ids = []
        for s in stubs:
            response = post(
                f"{self.__get_base_url()}{Urls.MAPPINGS}",
                json=s.get_mapping(),
                timeout=self.timeout,
            )
            self.attach_response(response)
            _id: str = response.json()["uuid"]
            stub.ids.append(_id)
        return stub

    def delete_stub(self, stub: Stub) -> None:
        """
        Delete a specific stub by its ID from the Wiremock server.

        :param stub: The ID of the stub to retrieve.
        :return: The HTTP response object.
        """
        for _id in stub.ids:
            response = delete(
                f"{self.__get_base_url()}{Urls.MAPPINGS}/{_id}", timeout=self.timeout
            )
            self.attach_response(response)

    def create_scenario(self, scenario: Scenario) -> list[Stub]:
        """
        Create a scenario with multiple stubs.

        :param scenario: The Scenario object containing multiple stubs to be created.
        :return: A list of Stub objects that were created.
        """
        for stub in scenario.scenario_stubs:
            self.create_stub(stub)
        return scenario.scenario_stubs

    def get_all_requests(self) -> WiremockRequestsHistoryModel:
        """
        Retrieve all requests made to the Wiremock server.

        :return: A Root object containing all requests.
        """
        response = get(self.__get_base_url() + Urls.REQUESTS, timeout=self.timeout)
        return WiremockRequestsHistoryModel(**response.json())

    def get_stub_requests(self, stub: Stub) -> Any:
        """
        Retrieve requests associated with a specific stub.

        :param stub: The Stub object whose requests are to be retrieved.
        :return: A collection of requests.
        """
        response = get(self.__get_base_url() + Urls.REQUESTS, timeout=self.timeout)

        for request in WiremockRequestsHistoryModel(**response.json()).requests:
            if request.request.headers is not None:
                for stub_id in stub.ids:
                    if (
                        request.response
                        and request.response.headers
                        and stub_id == request.request.headers.matched_stub_Id
                    ):
                        return request

    def clear_history(self) -> None:
        """
        Delete all requests history
        """
        delete(self.__get_base_url() + Urls.REQUESTS, timeout=self.timeout)

    def delete_request_by_id(self, request_id: str) -> None:
        """
        Delete a specific request from the Wiremock server by its ID.

        :param request_id: The unique identifier of the request to be deleted.
        """
        delete(
            self.__get_base_url() + Urls.REQUESTS + "/" + request_id,
            timeout=self.timeout,
        )

    def delete_stub_requests(self, stub: Stub) -> None:
        """
        Delete requests associated with a given stub.

        :param stub: The Stub object whose requests are to be deleted.
        """
        all_requests = get(
            f"{self.__get_base_url()}{Urls.REQUESTS}", timeout=self.timeout
        ).json()["requests"]
        stub_requests_ids = [
            request["id"]
            for request in all_requests
            if request["stubMapping"]["uuid"] in stub.ids
        ]
        for request_id in stub_requests_ids:
            self.delete_request_by_id(request_id)
