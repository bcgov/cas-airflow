from backoff import retry_with_backoff
import pytest

import logging
logger = logging.getLogger(__name__)

def test_backoff_raises_exception(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda x: None)

    with pytest.raises(Exception):
        retry_with_backoff(monkeypatch)

def test_backoff_passes():
    def mock_function():
        return 0
    assert 0 == retry_with_backoff(mock_function)
