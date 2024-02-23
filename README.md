## For developers

Clone a repository:
```bash
git clone https://github.com/gerzha/WireMockClientPy.git
cd qawiremock
```

Prepare an virtual environment:
```bash
virtualenv venv/wiremock --python=python3.11 --no-site-packages
source venv/wiremock/bin/activate
pip install -r requirements/requirements.txt
```

## About
This framework is based on WireMock and supports WireMock version 3.3.1.

WireMock offers an API for interaction; qawiremock simplifies the usage of this API by encapsulating it within a fluent interface, closely resembling the native API provided by WireMock itself.

It's important to note that qawiremock necessitates the operation of a standalone WireMock instance.


API
The API is based directly on WireMock's API, so see the WireMock documentation(https://wiremock.org/docs/overview/)
for general help with interacting with WireMock.


## Usage
```python
from qawiremock.client import WiremockClient, Stub, Scenario
from qawiremock.patterns import WireMockResponse, WireMockRequest
from  qawiremock import matchers


class WiremockSteps(object):
    def __init__(self, host, port):
        self.client = WiremockClient(host, port)

    def setup_stub(self):
        body = {'test': 'response'}

        request = WireMockRequest(
         method="POST",
         url="example",
         body_patterns=matchers.equal_to_json({"account_id": "1"}
                                              )
        )
        response = WireMockResponse(status=200, json_body=body)
        stub = Stub().when(request).reply(response)
        self.client.create_stub(stub)

    def setup_scenario(self):
     
        """
        Create scenario:
        1. Response 5 times with 500 error on the request
        2. Response on the 6 time positive 200 OK in the request
        """
     
        #create positive payload
        ok_body = {"test": "response"}
        
        #create negative payload
        error_body = {"error": "text_error"}
        
        #create request stub
        request = WireMockRequest(method="GET", url='ISteamUser/GetPublisherAppOwnership/v2/')
        
        #create error response setup for stub
        error_response = WireMockResponse(status=500, json_body=error_body)
        
        #create positive response setup for stub
        ok_response = WireMockResponse(status=200, json_body=ok_body)
        
        #create negative response stub
        error_stub = Stub().when(request).reply(response=error_response, times=5)
        
        #create positive response stub
        ok_stub = Stub().when(request).reply(ok_response)
     
        scen = Scenario()
        
        #place stub in the required order
        scen.scenario_stubs = [ok_stub, error_stub]
        
        #create scenario
        self.client.create_scenario(scen)
```

`conftest.py` module:
```python
import pytest

from project_qa.mock.steps import WiremockSteps


@pytest.fixture
def wiremock_steps():
    return WiremockSteps(host='<host from config>', port='<port from config>')
```