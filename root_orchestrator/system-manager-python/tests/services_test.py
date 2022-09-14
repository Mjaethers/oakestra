import sys
import unittest
import copy
from unittest.mock import MagicMock, patch, ANY

sys.modules['ext_requests.net_plugin_requests'] = unittest.mock.Mock()
net_plugin = sys.modules['ext_requests.net_plugin_requests']
net_plugin.net_inform_service_deploy = MagicMock()

import mongomock as mongomock
import pymongo
from ext_requests import mongodb_client, apps_db
from tests.utils import *
from services.service_management import create_services_of_app, generate_db_structure, delete_service

@mongomock.patch(servers=(('localhost', 10007),))
def test_create_service_with_app():
    # SETUP
    mockdb()

    sla = get_full_random_sla_app()
    db_app_mock = copy.deepcopy(sla)

    db_app_mock['applications'][0]['userId'] = 'Admin'
    db_app_mock['applications'][0]['microservices'] = []
    app_id = apps_db.mongo_add_application(db_app_mock['applications'][0])
    sla['applications'][0]['applicationID'] = app_id

    microservices = sla["applications"][0]['microservices']
    last_service = microservices[len(microservices) - 1]
    last_service = generate_db_structure(db_app_mock['applications'][0], last_service)

    # EXEC
    result, code = create_services_of_app("Admin", sla)

    # ASSERT
    assert code == 200
    db_app_result = apps_db.mongo_find_app_by_name_and_namespace(sla["applications"][0]["application_name"],
                                                                 sla["applications"][0]["application_namespace"])
    net_plugin.net_inform_service_deploy.assert_called_with(last_service, ANY)
    assert len(db_app_result['microservices']) == len(sla["applications"][0]['microservices'])


@mongomock.patch(servers=(('localhost', 10007),))
def test_create_service_without_app():
    # SETUP
    mockdb()
    sla = get_full_random_sla_app()
    sla['applications'][0]['applicationID'] = '63219606def3818062c12cd3'

    # EXEC
    result, code = create_services_of_app("Admin", sla)

    # ASSERT
    assert code == 404
    db_app_result = apps_db.mongo_find_app_by_name_and_namespace(sla["applications"][0]["application_name"],
                                                                 sla["applications"][0]["application_namespace"])
    assert db_app_result is None

@mongomock.patch(servers=(('localhost', 10007),))
def test_create_invalid_service_name():
    # SETUP
    mockdb()

    sla = get_full_random_sla_app()
    db_app_mock = copy.deepcopy(sla)

    db_app_mock['applications'][0]['userId'] = 'Admin'
    db_app_mock['applications'][0]['microservices'] = []
    app_id = apps_db.mongo_add_application(db_app_mock['applications'][0])
    sla['applications'][0]['applicationID'] = app_id

    sla['applications'][0]['microservices'][0]['microservice_name']="THISNAMEISTOOLONGTOBECCEPTED"

    # EXEC
    result, code = create_services_of_app("Admin", sla)

    # ASSERT
    assert code == 403

@mongomock.patch(servers=(('localhost', 10007),))
def test_create_invalid_service_name():
    # SETUP
    mockdb()

    sla = get_full_random_sla_app()
    db_app_mock = copy.deepcopy(sla)

    db_app_mock['applications'][0]['userId'] = 'Admin'
    db_app_mock['applications'][0]['microservices'] = []
    app_id = apps_db.mongo_add_application(db_app_mock['applications'][0])
    sla['applications'][0]['applicationID'] = app_id

    sla['applications'][0]['microservices'][0]['microservice_namespace']="THISNAMESPACEISTOOLONGTOBECCEPTED"

    # EXEC
    result, code = create_services_of_app("Admin", sla)

    # ASSERT
    assert code == 403

@mongomock.patch(servers=(('localhost', 10007),))
def test_delete_service():
    # SETUP
    mockdb()

    sla = get_full_random_sla_app()
    db_app_mock = copy.deepcopy(sla)

    db_app_mock['applications'][0]['userId'] = 'Admin'
    db_app_mock['applications'][0]['microservices'] = []
    app_id = apps_db.mongo_add_application(db_app_mock['applications'][0])
    sla['applications'][0]['applicationID'] = app_id

    result, code = create_services_of_app("Admin", sla)
    db_app_before_deletion = apps_db.mongo_find_app_by_name_and_namespace(sla["applications"][0]["application_name"],sla["applications"][0]["application_namespace"])
    service_to_be_deleted = db_app_before_deletion['microservices'][0]

    #EXEC
    result = delete_service('Admin',service_to_be_deleted)

    # ASSERT
    assert result
    db_app_after_deletion = apps_db.mongo_find_app_by_name_and_namespace(sla["applications"][0]["application_name"],sla["applications"][0]["application_namespace"])
    assert service_to_be_deleted not in db_app_after_deletion['microservices']
    assert apps_db.mongo_find_job_by_id(service_to_be_deleted) is None


def mockdb():
    mongodb_client.mongo_jobs = pymongo.MongoClient('mongodb://localhost:10007/jobs')
    mongodb_client.mongo_clusters = pymongo.MongoClient('mongodb://localhost:10007/clusters')
    mongodb_client.mongo_users = pymongo.MongoClient('mongodb://localhost:10007/users').db['user']
    mongodb_client.mongo_applications = mongodb_client.mongo_jobs.db['apps']
    mongodb_client.mongo_services = mongodb_client.mongo_jobs.db['jobs']
    mongodb_client.app = MagicMock()
