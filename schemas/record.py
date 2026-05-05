from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class RecordSave(BaseModel):
    user_id: int = Field(..., description="关联用户ID")
    music_id: int = Field(..., description="关联音乐ID")
    score: float = Field(..., ge=0, le=100, description="得分（0-100）")
    comment: Optional[str] = Field(default=None, description="评语")

class RecordSaveResponse(BaseModel):
    code: int = 200
    msg: str = "演唱记录保存成功"
    data: dict = {}

class RecordHistoryItem(BaseModel):
    record_time: datetime = Field(..., description="演唱时间")
    score: float = Field(..., description="演唱得分")
    song_name: str = Field(..., description="歌曲名称")
    nation: str = Field(..., description="所属民族")
    comment: Optional[str] = Field(default=None, description="AI评语")

class RecordHistoryResponse(BaseModel):
    code: int = 200
    msg: str = "查询成功"
    data: List[RecordHistoryItem] = []
