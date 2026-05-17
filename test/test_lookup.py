#!/usr/bin/env python3

import re

import aiohttp
import pytest
import requests
import xmltodict
from aioresponses import aioresponses as mock_aiohttp

from abn_lookup_service.lookup import ABNLookupClient


@pytest.fixture
def client():
    return ABNLookupClient(authentication_guid='test-guid-12345')


@pytest.fixture
def single_result_dict():
    return {
        'ABRPayloadSearchResults': {
            'response': {
                'businessEntity': {
                    'ABN':          {'identifierValue': '51824753556'},
                    'entityStatus': 'Active',
                    'mainName':     {'organisationName': 'Test Company'}
                }
            }
        }
    }


@pytest.fixture
def multiple_results_dict():
    return {
        'ABRPayloadSearchResults': {
            'response': {
                'searchResultsList': {
                    'searchResultsRecord': [
                        {'ABN': '51824753556', 'name': 'Test Company 1'},
                        {'ABN': '12345678901', 'name': 'Test Company 2'}
                    ]
                }
            }
        }
    }


def test_search_by_abn(client, single_result_dict, requests_mock):
    requests_mock.get(
        'https://abr.business.gov.au/ABRXMLSearchRPC/ABRXMLSearch.asmx/ABRSearchByABN',
        text=xmltodict.unparse(single_result_dict)
    )

    results = list(client.search_by_abn('51824753556'))

    assert len(results) == 1
    assert 'ABRPayloadSearchResults' in results[0]
    assert 'searchString=51824753556' in requests_mock.last_request.url
    assert 'authenticationGuid=test-guid-12345' in requests_mock.last_request.url


async def test_async_search_by_abn(client, single_result_dict):
    with mock_aiohttp() as m:
        m.get(re.compile(r'.*ABRSearchByABN.*'), body=xmltodict.unparse(single_result_dict).encode())
        result = await client.async_search_by_abn('51824753556')
        url = list(m.requests.keys())[0][1]

    assert 'ABRPayloadSearchResults' in result
    assert url.query['searchString'] == '51824753556'
    assert url.query['authenticationGuid'] == 'test-guid-12345'


def test_search_by_abn_with_history(client, single_result_dict, requests_mock):
    requests_mock.get(
        'https://abr.business.gov.au/ABRXMLSearchRPC/ABRXMLSearch.asmx/ABRSearchByABN',
        text=xmltodict.unparse(single_result_dict)
    )

    results = list(client.search_by_abn('51824753556', includeHistoricalDetails='Y'))

    assert len(results) == 1
    assert 'includeHistoricalDetails=Y' in requests_mock.last_request.url


async def test_async_search_by_abn_with_history(client, single_result_dict):
    with mock_aiohttp() as m:
        m.get(re.compile(r'.*ABRSearchByABN.*'), body=xmltodict.unparse(single_result_dict).encode())
        result = await client.async_search_by_abn('51824753556', includeHistoricalDetails='Y')
        url = list(m.requests.keys())[0][1]

    assert 'ABRPayloadSearchResults' in result
    assert url.query['includeHistoricalDetails'] == 'Y'


def test_search_by_asic(client, single_result_dict, requests_mock):
    requests_mock.get(
        'https://abr.business.gov.au/ABRXMLSearchRPC/ABRXMLSearch.asmx/ABRSearchByASIC',
        text=xmltodict.unparse(single_result_dict)
    )

    results = list(client.search_by_asic('123456789'))

    assert len(results) == 1
    assert 'searchString=123456789' in requests_mock.last_request.url


async def test_async_search_by_asic(client, single_result_dict):
    with mock_aiohttp() as m:
        m.get(re.compile(r'.*ABRSearchByASIC.*'), body=xmltodict.unparse(single_result_dict).encode())
        result = await client.async_search_by_asic('123456789')
        url = list(m.requests.keys())[0][1]

    assert 'ABRPayloadSearchResults' in result
    assert url.query['searchString'] == '123456789'
    assert url.query['authenticationGuid'] == 'test-guid-12345'


def test_search_by_name(client, multiple_results_dict, requests_mock):
    requests_mock.get(
        'https://abr.business.gov.au/ABRXMLSearchRPC/ABRXMLSearch.asmx/ABRSearchByNameSimpleProtocol',
        text=xmltodict.unparse(multiple_results_dict)
    )

    results = list(client.search_by_name('Test Company', state='NSW'))

    assert len(results) == 2
    assert results[0]['ABN'] == '51824753556'
    assert results[1]['ABN'] == '12345678901'
    assert 'name=Test+Company' in requests_mock.last_request.url
    assert 'NSW=Y' in requests_mock.last_request.url


async def test_async_search_by_name(client, multiple_results_dict):
    with mock_aiohttp() as m:
        m.get(re.compile(r'.*ABRSearchByNameSimpleProtocol.*'), body=xmltodict.unparse(multiple_results_dict).encode())
        results = [r async for r in client.async_search_by_name('Test Company', state='NSW')]
        url = list(m.requests.keys())[0][1]

    assert len(results) == 2
    assert results[0]['ABN'] == '51824753556'
    assert results[1]['ABN'] == '12345678901'
    assert url.query['name'] == 'Test Company'
    assert url.query['NSW'] == 'Y'


def test_search_by_name_advanced(client, multiple_results_dict, requests_mock):
    requests_mock.get(
        'https://abr.business.gov.au/ABRXMLSearchRPC/ABRXMLSearch.asmx/ABRSearchByNameAdvancedSimpleProtocol',
        text=xmltodict.unparse(multiple_results_dict)
    )

    results = list(client.search_by_name_advanced(
        'Test Company',
        postcode='2000',
        legalName='Y',
        searchWidth='Typical',
        minimumScore=80
    ))

    assert len(results) == 2
    assert 'name=Test+Company' in requests_mock.last_request.url
    assert 'postcode=2000' in requests_mock.last_request.url
    assert 'legalName=Y' in requests_mock.last_request.url
    assert 'searchWidth=Typical' in requests_mock.last_request.url
    assert 'minimumScore=80' in requests_mock.last_request.url


async def test_async_search_by_name_advanced(client, multiple_results_dict):
    with mock_aiohttp() as m:
        m.get(re.compile(r'.*ABRSearchByNameAdvancedSimpleProtocol.*'), body=xmltodict.unparse(multiple_results_dict).encode())
        results = [r async for r in client.async_search_by_name_advanced(
            'Test Company',
            postcode='2000',
            legalName='Y',
            searchWidth='Typical',
            minimumScore=80
        )]
        url = list(m.requests.keys())[0][1]

    assert len(results) == 2
    assert url.query['name'] == 'Test Company'
    assert url.query['postcode'] == '2000'
    assert url.query['legalName'] == 'Y'
    assert url.query['searchWidth'] == 'Typical'
    assert url.query['minimumScore'] == '80'


def test_search_by_postcode(client, requests_mock):
    mock_response = {
        'ABRPayloadSearchResults': {
            'response': {
                'abnList': {
                    'abn': [
                        {'value': '51824753556'},
                        {'value': '12345678901'}
                    ]
                }
            }
        }
    }
    requests_mock.get(
        'https://abr.business.gov.au/ABRXMLSearchRPC/ABRXMLSearch.asmx/SearchByPostcode',
        text=xmltodict.unparse(mock_response)
    )

    results = list(client.search_by_postcode('2000'))

    assert len(results) == 2
    assert 'postcode=2000' in requests_mock.last_request.url


async def test_async_search_by_postcode(client):
    mock_response = {
        'ABRPayloadSearchResults': {
            'response': {
                'abnList': {
                    'abn': [
                        {'value': '51824753556'},
                        {'value': '12345678901'}
                    ]
                }
            }
        }
    }
    with mock_aiohttp() as m:
        m.get(re.compile(r'.*SearchByPostcode.*'), body=xmltodict.unparse(mock_response).encode())
        results = [r async for r in client.async_search_by_postcode('2000')]
        url = list(m.requests.keys())[0][1]

    assert len(results) == 2
    assert url.query['postcode'] == '2000'


def test_search_by_abn_status(client, requests_mock):
    mock_response = {
        'ABRPayloadSearchResults': {
            'response': {
                'abnList': {
                    'abn': [
                        {'value': '51824753556'},
                        {'value': '12345678901'}
                    ]
                }
            }
        }
    }
    requests_mock.get(
        'https://abr.business.gov.au/ABRXMLSearchRPC/ABRXMLSearch.asmx/SearchByABNStatus',
        text=xmltodict.unparse(mock_response)
    )

    results = list(client.search_by_abn_status(postcode='2000', activeABNsOnly='Y'))

    assert len(results) == 2
    assert 'postcode=2000' in requests_mock.last_request.url
    assert 'activeABNsOnly=Y' in requests_mock.last_request.url


async def test_async_search_by_abn_status(client):
    mock_response = {
        'ABRPayloadSearchResults': {
            'response': {
                'abnList': {
                    'abn': [
                        {'value': '51824753556'},
                        {'value': '12345678901'}
                    ]
                }
            }
        }
    }
    with mock_aiohttp() as m:
        m.get(re.compile(r'.*SearchByABNStatus.*'), body=xmltodict.unparse(mock_response).encode())
        results = [r async for r in client.async_search_by_abn_status(postcode='2000', activeABNsOnly='Y')]
        url = list(m.requests.keys())[0][1]

    assert len(results) == 2
    assert url.query['postcode'] == '2000'
    assert url.query['activeABNsOnly'] == 'Y'


def test_search_by_update_event(client, requests_mock):
    mock_response = {
        'ABRPayloadSearchResults': {
            'response': {
                'abnList': {
                    'abn': [
                        {'value': '51824753556'},
                        {'value': '12345678901'}
                    ]
                }
            }
        }
    }
    requests_mock.get(
        'https://abr.business.gov.au/ABRXMLSearchRPC/ABRXMLSearch.asmx/SearchByUpdateEvent',
        text=xmltodict.unparse(mock_response)
    )

    results = list(client.search_by_update_event(
        updatedate='2020-01-01', postcode='3000', state='VIC'
    ))

    assert len(results) == 2
    assert 'updatedate=2020-01-01' in requests_mock.last_request.url
    assert 'postcode=3000' in requests_mock.last_request.url
    assert 'state=VIC' in requests_mock.last_request.url


async def test_async_search_by_update_event(client):
    mock_response = {
        'ABRPayloadSearchResults': {
            'response': {
                'abnList': {
                    'abn': [
                        {'value': '51824753556'},
                        {'value': '12345678901'}
                    ]
                }
            }
        }
    }
    with mock_aiohttp() as m:
        m.get(re.compile(r'.*SearchByUpdateEvent.*'), body=xmltodict.unparse(mock_response).encode())
        results = [r async for r in client.async_search_by_update_event(
            updatedate='2020-01-01', postcode='3000', state='VIC'
        )]
        url = list(m.requests.keys())[0][1]

    assert len(results) == 2
    assert url.query['updatedate'] == '2020-01-01'
    assert url.query['postcode'] == '3000'
    assert url.query['state'] == 'VIC'


def test_search_by_registration_event(client, requests_mock):
    mock_response = {
        'ABRPayloadSearchResults': {
            'response': {
                'abnList': {
                    'abn': [
                        {'value': '51824753556'},
                        {'value': '12345678901'}
                    ]
                }
            }
        }
    }
    requests_mock.get(
        'https://abr.business.gov.au/ABRXMLSearchRPC/ABRXMLSearch.asmx/SearchByRegistrationEvent',
        text=xmltodict.unparse(mock_response)
    )

    results = list(client.search_by_registration_event(
        month='1', year='2020', state='VIC', postcode='3000'
    ))

    assert len(results) == 2
    assert 'month=1' in requests_mock.last_request.url
    assert 'year=2020' in requests_mock.last_request.url
    assert 'state=VIC' in requests_mock.last_request.url
    assert 'postcode=3000' in requests_mock.last_request.url


async def test_async_search_by_registration_event(client):
    mock_response = {
        'ABRPayloadSearchResults': {
            'response': {
                'abnList': {
                    'abn': [
                        {'value': '51824753556'},
                        {'value': '12345678901'}
                    ]
                }
            }
        }
    }
    with mock_aiohttp() as m:
        m.get(re.compile(r'.*SearchByRegistrationEvent.*'), body=xmltodict.unparse(mock_response).encode())
        results = [r async for r in client.async_search_by_registration_event(
            month='1', year='2020', state='VIC', postcode='3000'
        )]
        url = list(m.requests.keys())[0][1]

    assert len(results) == 2
    assert url.query['month'] == '1'
    assert url.query['year'] == '2020'
    assert url.query['state'] == 'VIC'
    assert url.query['postcode'] == '3000'


def test_search_by_charity(client, requests_mock):
    mock_response = {
        'ABRPayloadSearchResults': {
            'response': {
                'abnList': {
                    'abn': [
                        {'value': '51824753556'},
                        {'value': '12345678901'}
                    ]
                }
            }
        }
    }
    requests_mock.get(
        'https://abr.business.gov.au/ABRXMLSearchRPC/ABRXMLSearch.asmx/SearchByCharity',
        text=xmltodict.unparse(mock_response)
    )

    results = list(client.search_by_charity(postcode='2000', state='NSW'))

    assert len(results) == 2
    assert 'postcode=2000' in requests_mock.last_request.url
    assert 'state=NSW' in requests_mock.last_request.url


async def test_async_search_by_charity(client):
    mock_response = {
        'ABRPayloadSearchResults': {
            'response': {
                'abnList': {
                    'abn': [
                        {'value': '51824753556'},
                        {'value': '12345678901'}
                    ]
                }
            }
        }
    }
    with mock_aiohttp() as m:
        m.get(re.compile(r'.*SearchByCharity.*'), body=xmltodict.unparse(mock_response).encode())
        results = [r async for r in client.async_search_by_charity(postcode='2000', state='NSW')]
        url = list(m.requests.keys())[0][1]

    assert len(results) == 2
    assert url.query['postcode'] == '2000'
    assert url.query['state'] == 'NSW'


def test_state_flags_generation(client, multiple_results_dict, requests_mock):
    requests_mock.get(
        'https://abr.business.gov.au/ABRXMLSearchRPC/ABRXMLSearch.asmx/ABRSearchByNameSimpleProtocol',
        text=xmltodict.unparse(multiple_results_dict)
    )

    list(client.search_by_name('Test', state='VIC'))

    url = requests_mock.last_request.url
    assert 'VIC=Y' in url
    assert 'NSW=N' in url
    assert 'QLD=N' in url


def test_http_error_handling(client, requests_mock):
    requests_mock.get(
        'https://abr.business.gov.au/ABRXMLSearchRPC/ABRXMLSearch.asmx/ABRSearchByABN',
        status_code=404,
        text='Not Found'
    )

    with pytest.raises(requests.exceptions.HTTPError):
        list(client.search_by_abn('invalid'))


async def test_async_http_error_handling(client):
    with mock_aiohttp() as m:
        m.get(re.compile(r'.*ABRSearchByABN.*'), status=404, body=b'Not Found')
        with pytest.raises(aiohttp.ClientResponseError):
            await client.async_search_by_abn('invalid')
