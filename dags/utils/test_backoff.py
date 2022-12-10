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
    def mock_function(x):
        return x
    assert 8 == retry_with_backoff(lambda: mock_function(8))
    assert "word" == retry_with_backoff(lambda: mock_function("word"))
    assert None == retry_with_backoff(lambda: mock_function(None))
