import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from main import app
from db_config import get_db

@pytest.fixture(scope="function")
def mock_db():
    db = MagicMock()
    cursor = MagicMock()
    # 保证 db.cursor() 总是返回我们的 mock cursor
    db.cursor.return_value = cursor
    return db, cursor

@pytest.fixture(scope="function")
def client(mock_db):
    db, _ = mock_db
    
    def override_get_db():
        yield db
        
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
