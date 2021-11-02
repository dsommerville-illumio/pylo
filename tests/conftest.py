import json
import os

import pylo
import pytest

TESTS_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(TESTS_DIR, 'data')

pylo.log_set_debug()


@pytest.fixture(scope='session')
def pce_data():
    with open(os.path.join(DATA_DIR, 'pce_data.json'), 'r+') as json_file:
        pce_objects = json.loads(json_file.read())
    return pce_objects


@pytest.fixture(scope='session')
def mock_pce(pce_data):
    org = pylo.Organization(49)
    org.pce_version = pylo.SoftwareVersion(pce_data['pce_version'])
    org.load_from_json(pce_data['data'])
    yield org
