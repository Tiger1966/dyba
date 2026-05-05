import time
from fastapi import APIRouter, Depends, HTTPException, Request
from schemas.user import UserRegister, UserRegisterResponse, UserRegisterData
from dao.user import register_or_login
from db_config import get_db

router = APIRouter()

# 简单的基于内存的限流器
# 限制：同一 IP 1 分钟最多 20 次请求
# 使用字典存储 {ip: [timestamps]}
rate_limit_store = {}

def check_rate_limit(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    current_time = time.time()
    
    # 清理一分钟前的记录
    if client_ip in rate_limit_store:
        rate_limit_store[client_ip] = [
            ts for ts in rate_limit_store[client_ip] 
            if current_time - ts < 60
        ]
    else:
        rate_limit_store[client_ip] = []
        
    if len(rate_limit_store[client_ip]) >= 20:
        raise HTTPException(status_code=429, detail={"code": 429, "msg": "请求过于频繁"})
        
    rate_limit_store[client_ip].append(current_time)

@router.post("/api/register", response_model=UserRegisterResponse)
def register(
    user: UserRegister, 
    request: Request,
    db = Depends(get_db)
):
    check_rate_limit(request)
    
    user_id = register_or_login(db, user.phone, user.password)
    
    return UserRegisterResponse(
        code=200,
        msg="注册/登录成功",
        data=UserRegisterData(user_id=user_id)
    )
