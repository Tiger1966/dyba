from pydantic import BaseModel
from typing import Optional

class AnalyzeResponseData(BaseModel):
    music_id: int
    nation: str
    song_name: str
    video_url: Optional[str] = None
    ref_audio_url: Optional[str] = None
    temperament_tags: Optional[list[str]] = None
    science_copy: Optional[str] = None

class AnalyzeResponse(BaseModel):
    code: int = 200
    msg: str = "分析成功"
    data: Optional[AnalyzeResponseData] = None
