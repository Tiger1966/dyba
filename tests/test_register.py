import pytest
from unittest.mock import ANY
from fastapi import HTTPException
import mysql.connector

from dao.user import register_or_login, hash_password
from schemas.user import UserRegister

def test_unit_phone_not_exists_insert(mock_db):
    """单元测试：手机号不存在插入"""
    db, cursor = mock_db
    cursor.fetchone.return_value = None
    cursor.lastrowid = 1
    
    user_id = register_or_login(db, "13800138000", "Password123")
    assert user_id == 1
    cursor.execute.assert_any_call(
        "INSERT INTO users(phone, password_hash, created_at) VALUES (%s, %s, now())",
        ("13800138000", ANY)
    )
    db.commit.assert_called()

def test_unit_exists_login(mock_db):
    """单元测试：已存在登录"""
    db, cursor = mock_db
    pwd_hash = hash_password("Password123")
    cursor.fetchone.return_value = (2, pwd_hash)
    
    user_id = register_or_login(db, "13800138001", "Password123")
    assert user_id == 2
    db.commit.assert_called()

def test_unit_wrong_password(mock_db):
    """单元测试：密码错误"""
    db, cursor = mock_db
    pwd_hash = hash_password("Password123")
    cursor.fetchone.return_value = (3, pwd_hash)
    
    with pytest.raises(HTTPException) as exc_info:
        register_or_login(db, "13800138002", "WrongPass1")
    
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["msg"] == "密码错误"
    db.rollback.assert_called()

def test_unit_param_validation_fail():
    """单元测试：参数校验失败"""
    with pytest.raises(ValueError):
        UserRegister(phone="13800138000", password="123")
        
    with pytest.raises(ValueError):
        UserRegister(phone="13800138000", password="Password")
        
    with pytest.raises(ValueError):
        UserRegister(phone="123", password="Password123")

def test_unit_db_connection_exception(mock_db):
    """单元测试：数据库连接异常"""
    db, cursor = mock_db
    cursor.execute.side_effect = Exception("DB Error")
    
    with pytest.raises(Exception, match="DB Error"):
        register_or_login(db, "13800138000", "Password123")
    db.rollback.assert_called()

# --- 集成测试 ---

def test_integration_register_success(client, mock_db):
    """集成测试：验证返回格式和状态码"""
    db, cursor = mock_db
    cursor.fetchone.return_value = None
    cursor.lastrowid = 10
    
    response = client.post("/api/register", json={
        "phone": "13900139000",
        "password": "ValidPassword123"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["msg"] == "注册/登录成功"
    assert data["data"]["user_id"] == 10

def test_integration_register_conflict(client, mock_db):
    """集成测试：唯一冲突（并发注册模拟）"""
    db, cursor = mock_db
    cursor.fetchone.return_value = None
    
    def mock_execute(query, params=None):
        if "INSERT" in query:
            raise mysql.connector.IntegrityError("Duplicate entry")
            
    cursor.execute.side_effect = mock_execute
    
    response = client.post("/api/register", json={
        "phone": "13900139002",
        "password": "ValidPassword123"
    })
    assert response.status_code == 409
    assert response.json()["code"] == 409
    assert response.json()["msg"] == "手机号已存在"

def test_integration_validation_error(client):
    """集成测试：参数校验错误"""
    response = client.post("/api/register", json={
        "phone": "invalid",
        "password": "short"
    })
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data

def test_integration_rate_limit(client, mock_db):
    """集成测试：限流"""
    from router.register import rate_limit_store
    rate_limit_store.clear()
    
    db, cursor = mock_db
    cursor.fetchone.return_value = None
    cursor.lastrowid = 1
    
    # 连续发送 20 次正常请求
    for i in range(20):
        response = client.post("/api/register", json={
            "phone": f"139001391{i:02d}",
            "password": "ValidPassword123"
        })
        assert response.status_code == 200
    
    # 第 21 次应该被限流
    response = client.post("/api/register", json={
        "phone": "13900139200",
        "password": "ValidPassword123"
    })
    assert response.status_code == 429
    assert response.json()["code"] == 429
    assert response.json()["msg"] == "请求过于频繁"
