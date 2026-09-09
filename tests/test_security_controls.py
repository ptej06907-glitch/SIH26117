import time

from backend.network import Monitor, allowed


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
