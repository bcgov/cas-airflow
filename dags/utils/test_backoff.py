from backoff import retry_with_backoff
import pytest

# run this test with
# pytest -s -p no:logging test_backoff.py
# to see logging during backoff process
def test_backoff_raises_exception(monkeypatch):
    # skip actual sleep time
    monkeypatch.setattr("time.sleep", lambda x: None)
    with pytest.raises(Exception):
        retry_with_backoff(monkeypatch)

def test_backoff_passes():
    def mock_function():
        return 0
    assert 0 == retry_with_backoff(mock_function)
