import pytest
from app import convert_objectid_to_str, load_api_keys
from bson import ObjectId

def test_convert_objectid_to_str():
    doc = {'_id': ObjectId(), 'name': 'John Doe'}
    result = convert_objectid_to_str(doc)
    assert isinstance(result['_id'], str)

def test_load_api_keys():
    api_key, who_is_key = load_api_keys()
    assert api_key is not None
    assert who_is_key is not None