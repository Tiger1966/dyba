import uvicorn
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import bcrypt
import mysql.connector
from db_config import connection_pool
from schemas.user import UserRegister, UserRegisterResponse, UserRegisterData
from schemas.analyze import AnalyzeResponse, AnalyzeResponseData
from fastapi import HTTPException
from router import record, analyze
from fastapi.staticfiles import StaticFiles

# 实例化 FastAPI
app = FastAPI(title="Dianyin Backend API")

# 挂载静态目录
app.mount("/static", StaticFiles(directory="static"), name="static")

# 注册路由
app.include_router(record.router, prefix="/api")
app.include_router(analyze.router, prefix="/api")

# 配置 CORS 跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/register", response_model=UserRegisterResponse)
def register(user: UserRegister):
    # 如果连接池没有初始化成功
    if not connection_pool:
        raise HTTPException(status_code=500, detail={"code": 500, "msg": "数据库连接池未初始化"})
        
    conn = None
    cursor = None
    try:
        # 1. 从连接池获取连接
        conn = connection_pool.get_connection()
        cursor = conn.cursor()
        
        phone = user.phone
        password = user.password
        
        # 2. 查询用户并加锁 (查 users 表)
        cursor.execute("SELECT id, password_hash FROM users WHERE phone = %s FOR UPDATE", (phone,))
        user_record = cursor.fetchone()
        
        if user_record:
            # 3. 有就验证密码，成功则返回 user_id
            user_id = user_record[0]
            stored_hash = user_record[1]
            
            if not bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
                raise HTTPException(status_code=401, detail={"code": 401, "msg": "密码错误"})
                
            conn.commit()
            return UserRegisterResponse(
                code=200, 
                msg="注册/登录成功", 
                data=UserRegisterData(user_id=user_id)
            )
        else:
            # 4. 没有就 INSERT 进去再返回新 user_id
            # 生成 bcrypt 哈希
            salt = bcrypt.gensalt(rounds=12)
            pwd_hash = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
            
            try:
                insert_query = "INSERT INTO users(phone, password_hash, created_at) VALUES (%s, %s, now())"
                cursor.execute(insert_query, (phone, pwd_hash))
                new_user_id = cursor.lastrowid
                conn.commit()
                
                return UserRegisterResponse(
                    code=200, 
                    msg="注册/登录成功", 
                    data=UserRegisterData(user_id=new_user_id)
                )
            except mysql.connector.IntegrityError:
                # 处理并发情况下的唯一索引冲突
                raise HTTPException(status_code=409, detail={"code": 409, "msg": "手机号已存在"})
                
    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail={"code": 500, "msg": "服务器内部错误"})
    finally:
        # 5. 在 finally 里调用 conn.close() 把连接还给池子，防止池子枯竭
        if cursor:
            cursor.close()
        if conn:
            conn.close()

from fastapi.exceptions import RequestValidationError
from fastapi import Request
from fastapi.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request, exc):
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

# GET / 健康检查接口
@app.get("/")
def health_check():
    return JSONResponse(
        status_code=200,
        content={"status": "running"}
    )

# 启动脚本
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
