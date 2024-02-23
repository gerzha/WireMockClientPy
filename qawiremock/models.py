from typing import Any

from pydantic import BaseModel, Extra, Field, field_validator
from pydantic_core.core_schema import ValidationInfo
from wiremock.resources.mappings import CommonHeaders


class Header(BaseModel):
    host: str | None = None
    content_type: str | None = Field(None, serialization_alias="Content-Type")
    accept: str | None = None
    user_agent: str | None = Field(None, serialization_alias="User-Agent")
    authorization: str | None = None
    accept_encoding: str | None = Field(None, serialization_alias="Accept-Encoding")
    content_length: int | None = Field(None, serialization_alias="Content-Length")
    connection: str | None = Field(None, serialization_alias="Connection")
    matched_stub_Id: str | None = Field(None, serialization_alias="Matched-Stub-Id")

    class Config:
        extra = Extra.allow


class StubMappingRequestHistory(BaseModel):
    url: str | None = None
    absolute_url: str | None = Field(None, alias="absoluteUrl")
    method: str | None = None
    client_ip: str | None = Field(None, alias="clientIp")
    headers: Header | None = None
    cookies: dict[str, Any] | None = None
    browser_proxy_request: bool | None = Field(None, alias="browserProxyRequest")
    logged_date: int | None = Field(None, alias="loggedDate")
    body_as_base64: str | None = Field(None, alias="bodyAsBase64")
    body_patterns: list[Any] | None = Field(None, alias="bodyPatterns")
    logged_date_string: str | None = Field(None, alias="loggedDateString")
    query_params: dict[str, Any] | None = Field(None, alias="queryParams")
    form_params: dict[str, Any] | None = Field(None, alias="formParams")


class ResponseDefinition(BaseModel):
    status: int | None
    body: str | None = None
    headers: Header | None = None
    transformers: list[str] | None = None

    class Config:
        extra = Extra.allow


class WireMockResponse(BaseModel):
    status: int | None
    headers: dict[str, Any] = {CommonHeaders.CONTENT_TYPE: "application/json"}
    body_as_base64: str | None = Field(None, serialization_alias="bodyAsBase64")
    json_body: dict[str, Any] | str | None = Field(None, serialization_alias="jsonBody")
    transformers: list[str] | None = ["response-template"]
    fixed_delay_milliseconds: int | None = Field(
        0, serialization_alias="fixedDelayMilliseconds"
    )


class StubMapping(BaseModel):
    id: str | None
    request: StubMappingRequestHistory | None
    response: WireMockResponse | None
    uuid: str | None
    scenario_name: str | None = Field(None, alias="scenarioName")
    required_scenario_state: str | None = Field(None, alias="requiredScenarioState")
    new_scenario_state: str | None = Field(None, alias="newScenarioState")


class TimingRequestHistory(BaseModel):
    add_delay: int = Field(alias="addedDelay")
    process_time: int = Field(alias="processTime")
    response_send_time: int = Field(alias="responseSendTime")
    serve_time: int = Field(alias="serveTime")
    total_time: int = Field(alias="totalTime")


class RequestsHistoryModel(BaseModel):
    id: str
    request: StubMappingRequestHistory
    response_definition: ResponseDefinition = Field(alias="responseDefinition")
    response: WireMockResponse | None
    was_matched: bool = Field(alias="wasMatched")
    timing: TimingRequestHistory
    sub_events: list[Any] = Field(alias="subEvents")
    stub_mapping: StubMapping = Field(alias="stubMapping")


class Meta(BaseModel):
    total: int | None


class WiremockRequestsHistoryModel(BaseModel):
    requests: list[RequestsHistoryModel]
    meta: Meta
    request_journal_disabled: bool = Field(alias="requestJournalDisabled")


class RequestMappingModel(BaseModel):
    meta: Meta
    mappings: list[StubMapping]


class Matcher(BaseModel):
    contains: str | None = None
    equal_to: str | None = Field(None, serialization_alias="equalTo")
    matches_regex: str | None = Field(None, serialization_alias="matches")
    does_not_match_regex: str | None = Field(None, serialization_alias="doesNotMatch")
    equal_to_json: dict[str, Any] | None = Field(
        None, serialization_alias="equalToJson"
    )
    ignore_array_order: bool | None = Field(
        None, serialization_alias="ignoreArrayOrder"
    )
    case_insensitive: bool | None = Field(None, serialization_alias="caseInsensitive")
    ignore_external_elements: bool | None = Field(
        None, serialization_alias="ignoreExtraElements"
    )
    absent: bool | None = Field(None, serialization_alias="absent")


class WireMockRequest(BaseModel):
    url: str | None = None
    url_path_pattern: str | None = Field(None, serialization_alias="urlPathPattern")
    method: str | None = None
    headers: dict[str, str] = {}
    cookies: dict[str, str] = {}
    parameters: dict[str, str] | None = Field(
        None, serialization_alias="queryParameters"
    )
    stub_status: str | None = None
    body_patterns: list[Matcher] = Field(None, serialization_alias="bodyPatterns")

    class Config:
        extra = Extra.allow

    @field_validator("url", "url_path_pattern")  # noqa
    @classmethod
    def validate_url(cls, url: str, info: ValidationInfo) -> str:
        version = info.data.get("version", "v1")
        if not url:
            raise ValueError("URL must be specified")
        if version:
            url = f"/api/{version.strip('/')}/{url}/"
        elif not url.startswith("/"):
            url = f"/{url}"

        return url


class MappingModel(BaseModel):
    request: WireMockRequest
    response: WireMockResponse


class LogStubDataModel(BaseModel):
    url: str | None = None
    method: str | None = None
    status_code: int | None = None
    status: str | None = None
    headers: dict[str, str] | None
    cookies: dict[str, str] | None = None
    parameters: dict[str, str] | None = None
    json_body: dict[str, Any] | str | None = Field(None, serialization_alias="jsonBody")
    delay: int | None = None
    stub_status: str | None = None
    fixed_delay_milliseconds: int | None = None
    transformers: list[Any] | None = None
    body_patterns: list[Matcher] | None = None
    body: dict[str, Any] | str | None = None
