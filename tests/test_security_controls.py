import time

from backend.network import Monitor, allowed
from backend import vault


def test_network_policy_allows_only_loopback(tmp_path):
    assert allowed('127.0.0.1')
    assert allowed('::1')
    assert not allowed('8.8.8.8')
    monitor = Monitor(tmp_path / 'network.json')
    monitor.start()
    time.sleep(0.05)
    snapshot = monitor.snapshot()
    monitor.close()
    assert snapshot['python_guard'] is True
    assert snapshot['packet_capture'] == 'not_collected'
    assert 'connection snapshots' in snapshot['scope']


def test_network_observation_uses_encrypted_vault_when_enabled(tmp_path):
    (tmp_path / '.encrypted-storage').touch()
    path = tmp_path / 'network.json'
    monitor = Monitor(path)
    monitor.start()
    time.sleep(0.65)
    monitor.close()
    assert path.read_bytes().startswith(vault.MAGIC)
    assert b'python_guard' in vault.read_bytes(path)
