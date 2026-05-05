import mysql.connector
from fastapi import HTTPException

def insert_record(db_conn, user_id: int, music_id: int, score: float, comment: str):
    cursor = None
    try:
        cursor = db_conn.cursor()
        
        insert_query = """
            INSERT INTO records 
            (user_id, music_id, total_score, ai_comment, record_time, created_at) 
            VALUES (%s, %s, %s, %s, now(), now())
        """
        cursor.execute(insert_query, (
            user_id, 
            music_id, 
            score, 
            comment
        ))
        record_id = cursor.lastrowid
        
        db_conn.commit()
        return record_id
    except mysql.connector.IntegrityError as e:
        db_conn.rollback()
        print(f"Integrity Error: {e}")
        raise HTTPException(status_code=400, detail={"code": 400, "msg": "无效的 user_id 或 music_id"})
    except Exception as e:
        db_conn.rollback()
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail={"code": 500, "msg": "服务器内部错误"})
    finally:
        if cursor:
            cursor.close()

def get_user_history(db_conn, user_id: int):
    cursor = None
    try:
        # 使用 dictionary=True 让返回结果为字典列表
        cursor = db_conn.cursor(dictionary=True)
        
        query = """
            SELECT 
                r.record_time,
                r.total_score as score,
                m.song_name,
                m.nation,
                r.ai_comment as comment
            FROM records r
            JOIN music_dict m ON r.music_id = m.id
            WHERE r.user_id = %s
            ORDER BY r.record_time DESC
        """
        
        cursor.execute(query, (user_id,))
        records = cursor.fetchall()
        return records
        
    except Exception as e:
        print(f"Database error when fetching history: {e}")
        raise HTTPException(status_code=500, detail={"code": 500, "msg": "查询历史记录失败"})
    finally:
        if cursor:
            cursor.close()
