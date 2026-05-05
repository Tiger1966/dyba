from fastapi import APIRouter, Depends, HTTPException, Path, UploadFile, File, Form
from schemas.record import RecordSaveResponse, RecordHistoryResponse
from dao.record import insert_record, get_user_history
from db_config import get_db, connection_pool
import os
import shutil
import uuid
from scoring import get_score_and_comment
from utils.audio import AudioTranslator, AudioNormalizeError

router = APIRouter()

TEMP_DIR = "./uploads"
os.makedirs(TEMP_DIR, exist_ok=True)

@router.post("/save_record", response_model=RecordSaveResponse)
async def save_record(
    audio_file: UploadFile = File(...),
    user_id: int = Form(...),
    music_id: int = Form(...)
):
    if not connection_pool:
        raise HTTPException(status_code=500, detail="数据库连接池未初始化")
        
    file_ext = audio_file.filename.split('.')[-1] if '.' in audio_file.filename else 'wav'
    temp_filename = f"{uuid.uuid4().hex}.{file_ext}"
    temp_path = os.path.join(TEMP_DIR, temp_filename)
    
    conn = None
    norm_path = os.path.join(TEMP_DIR, f"norm_{uuid.uuid4().hex}.wav")
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
            
        # 使用 FFmpeg 转码并标准化音频
        try:
            AudioTranslator.normalize_to_wav(temp_path, norm_path)
        except AudioNormalizeError as e:
            raise HTTPException(status_code=400, detail=str(e))
            
        # 获得真实的打分和评语，使用转码后的文件
        score_data = get_score_and_comment(norm_path, music_id)
        score = score_data["score"]
        comment = score_data["comment"]
        
        conn = connection_pool.get_connection()
        record_id = insert_record(
            db_conn=conn,
            user_id=user_id,
            music_id=music_id,
            score=score,
            comment=comment
        )
        
        # 返回结果加入额外的科普与音色数据，以及调试字段
        return RecordSaveResponse(
            code=200,
            msg="演唱记录保存成功",
            data={
                "score": score, 
                "comment": comment, 
                "record_id": record_id,
                "science_copy": score_data.get("science_copy"),
                "timbre": score_data.get("timbre"),
                "score_mode": score_data.get("score_mode"),
                "fallback_reason": score_data.get("fallback_reason"),
                "debug_info": score_data.get("debug_info")
            }
        )
    except HTTPException:
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        print("Record save error details:")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="保存记录失败")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if conn:
            conn.close()

@router.get("/history/{user_id}", response_model=RecordHistoryResponse)
def get_history(
    user_id: int = Path(..., description="用户ID"),
    db = Depends(get_db)
):
    records = get_user_history(db_conn=db, user_id=user_id)
    
    return RecordHistoryResponse(
        code=200,
        msg="查询成功",
        data=records
    )
