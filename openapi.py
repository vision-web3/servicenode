import json
import os
import sys
from pathlib import Path

from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin
from flasgger import APISpec  # type: ignore
from flasgger import Swagger

from vision.servicenode.restapi import _BidSchema
from vision.servicenode.restapi import _BidsSchema
from vision.servicenode.restapi import _TransferResponseSchema
from vision.servicenode.restapi import _TransferSchema
from vision.servicenode.restapi import _TransferStatusResponseSchema
from vision.servicenode.restapi import _TransferStatusSchema
from vision.servicenode.restapi import flask_app

DOCS_PATH = "docs/openapi.json"

if len(sys.argv) > 1:
    DOCS_PATH = sys.argv[1]

plugins = [FlaskPlugin(), MarshmallowPlugin()]
spec = APISpec("Vision Service Node APISpec", '1.0', "3.0.2", plugins=plugins)

template = spec.to_flasgger(
    flask_app, definitions=[
        _BidSchema, _BidsSchema, _TransferSchema, _TransferResponseSchema,
        _TransferStatusSchema, _TransferStatusResponseSchema
    ])

swagger = Swagger(flask_app, template=template, parse=True)

with flask_app.test_request_context():
    data = swagger.get_apispecs()
    data.pop('definitions')
    data.pop('swagger')
    data['servers'] = [{'url': 'https://sn1.testnet.vision.io'}]

    if not (Path.cwd() / DOCS_PATH).exists():
        os.makedirs(os.path.dirname(DOCS_PATH), exist_ok=True)

    with open(DOCS_PATH, "w") as f:
        f.write(json.dumps(data, indent=4))
