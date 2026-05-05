import bcrypt
from fastapi import HTTPException
import mysql.connector

def get_user_for_update(cursor, phone: str):
    """查询用户并加锁"""
    # 原始 SQL 查询
    query = "SELECT id, password_hash FROM users WHERE phone = %s FOR UPDATE"
    cursor.execute(query, (phone,))
    return cursor.fetchone()

def check_password(plain_password: str, hashed_password: str) -> bool:
    """校验密码"""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def hash_password(password: str) -> str:
    """哈希密码"""
    # bcrypt 默认 cost 是 12
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def register_or_login(db: mysql.connector.connection.MySQLConnection, phone: str, password: str) -> int:
    """注册或登录逻辑（事务内执行）"""
    cursor = None
    try:
        # 使用 dictionary=False，返回元组，防止数据结构解析错误
        cursor = db.cursor()
        
        # a) SELECT id, password_hash FROM users WHERE phone = %s FOR UPDATE;
        user_record = get_user_for_update(cursor, phone)
        
        if user_record:
            # b) 若记录存在，校验 password 与存储的 password_hash
            user_id = user_record[0]
            stored_hash = user_record[1]
            if not check_password(password, stored_hash):
                raise HTTPException(status_code=401, detail={"code": 401, "msg": "密码错误"})
            db.commit()
            return user_id
        else:
            # c) 若记录不存在，生成 bcrypt 哈希后的 password_hash，执行 INSERT
            pwd_hash = hash_password(password)
            
            try:
                # 使用原始 SQL 插入，不支持 RETURNING 的版本可以使用 lastrowid 获取
                insert_query = "INSERT INTO users(phone, password_hash, created_at) VALUES (%s, %s, now())"
                cursor.execute(insert_query, (phone, pwd_hash))
                user_id = cursor.lastrowid
            except mysql.connector.IntegrityError:
                raise HTTPException(status_code=409, detail={"code": 409, "msg": "手机号已存在"})
            
            db.commit()
            return user_id
            
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise e
    finally:
        if cursor:
            cursor.close()
