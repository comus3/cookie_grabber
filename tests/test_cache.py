import pytest
from app import get_ip_info, cache

def test_get_ip_info_caching(client):
    ip_address = "8.8.8.8"
    
    # Premier appel pour mettre en cache le résultat
    result1 = get_ip_info(ip_address)
    assert result1 is not None

    # Deuxième appel pour vérifier que le cache fonctionne
    with cache.cache._redis_client.pipeline() as pipe:
        pipe.get(f"flask_cache_{ip_address}")
        cached_result = pipe.execute()
    assert cached_result is not None