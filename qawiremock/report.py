import json
from typing import Any
from urllib.parse import parse_qsl, urlsplit

import allure
from requests import Response

from qawiremock.models import LogStubDataModel, WireMockRequest, WireMockResponse


class Logger:
    @classmethod
    def pretty_json(cls, value: Any) -> str:
        return json.dumps(value, ensure_ascii=True, indent=4, sort_keys=True)

    @staticmethod
    def _parse_response_body(response: Response) -> dict[str, Any] | None:
        """Parse the JSON response body,
        returning None if parsing fails or not a dictionary."""
        try:
            body = response.json()
            if isinstance(body, dict):
                return body
            return None
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _parse_cookies(response: Response) -> dict[str, str]:
        """Extract cookies from the response."""
        return {
            cookie.name: cookie.value if cookie.value is not None else ""
            for cookie in response.cookies
        }

    @staticmethod
    def _parse_query_parameters(url: str | None) -> dict[str, str]:
        """Extract query parameters from the response URL."""
        if url is None:
            return {}
        return dict(parse_qsl(urlsplit(url).query))

    @classmethod
    def _attach_json_response(cls, dump_response: LogStubDataModel) -> None:
        """Attach JSON response to the report."""
        prepared_data: str = cls.pretty_json(dump_response.model_dump())
        attachment_name = f"HTTP Response - {prepared_data}"
        allure.attach(prepared_data, attachment_name, allure.attachment_type.JSON)

    @staticmethod
    def _attach_html_response(response: Response) -> None:
        """Attach HTML response to the report."""
        attachment_name = (
            f"Response (as HTML) - {response.status_code} {response.request.path_url}"
        )
        allure.attach(response.text, attachment_name, allure.attachment_type.HTML)

    @classmethod
    def attach_response(cls, response: Response) -> None:
        """Process and attach the response to the report."""
        content_type: str | None = response.headers.get("Content-Type")

        if content_type and content_type.startswith("application/json"):
            body = cls._parse_response_body(response)
            cookies = cls._parse_cookies(response)
            query_parameters = cls._parse_query_parameters(response.request.url)

            dump_response = LogStubDataModel(
                url=response.request.url,
                method=response.request.method,
                status_code=response.status_code,
                headers=dict(response.headers),
                json_body=body,
                cookies=cookies,
                parameters=query_parameters,
            )

            cls._attach_json_response(dump_response)

        if content_type and content_type.startswith("text/html"):
            cls._attach_html_response(response)

    @classmethod
    def attach_stub_response(cls, response: WireMockResponse) -> None:
        dump_response = LogStubDataModel(
            status_code=response.status,
            headers=dict(response.headers),
            json_body=response.json_body,
            fixed_delay_milliseconds=response.fixed_delay_milliseconds,
            transformers=response.transformers,
        )
        cls._attach_json_response(dump_response)

    @classmethod
    def attach_stub_request(cls, request: WireMockRequest) -> None:
        dump_response = LogStubDataModel(
            url=request.url,
            method=request.method,
            headers=dict(request.headers),
            cookies=dict(request.cookies),
            parameters=request.parameters,
            body_patterns=request.body_patterns,
            json_body=None,
        )
        cls._attach_json_response(dump_response)
