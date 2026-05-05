import librosa
import numpy as np
import asyncio
import logging
import os
import httpx
import traceback
from config.ai_prompt import YUNNAN_STYLE_PROMPT
from metadata import SONG_METADATA

logger = logging.getLogger(__name__)

def get_ref_path(song_id: int) -> str:
    return f"/www/wwwroot/dianyin_app/static/references/{song_id}.wav"

def get_score_and_comment(user_audio_path: str, song_id: int) -> dict:
    """
    计算得分并返回相应的评分话术、科普文案和音色匹配逻辑。
    """
    score_mode = "computed"
    fallback_reason = None
    debug_info = {"user_audio_len": 0, "ref_audio_len": 0}

    try:
        ref_audio = get_ref_path(song_id)
        if not os.path.exists(ref_audio):
            score_mode = "fallback"
            fallback_reason = "系统找不到对应的参考音频"
            
        # 提取基频F0，处理可能的异常
        try:
            y1, sr = librosa.load(user_audio_path, sr=16000)
            if not os.path.exists(ref_audio):
                y2 = np.array([])
            else:
                y2, _ = librosa.load(ref_audio, sr=16000)
            
            debug_info["user_audio_len"] = len(y1)
            debug_info["ref_audio_len"] = len(y2)
            
            if len(y1) == 0 or len(y2) == 0:
                f0_1, f0_2 = [], []
                if score_mode != "fallback":
                    score_mode = "fallback"
                    fallback_reason = "音频文件为空或加载失败"
            else:
                f0_1, _, _ = librosa.pyin(y1, fmin=80, fmax=450, sr=sr)
                f0_2, _, _ = librosa.pyin(y2, fmin=80, fmax=450, sr=sr)
                
                f0_1 = f0_1[~np.isnan(f0_1)]
                f0_2 = f0_2[~np.isnan(f0_2)]
        except Exception as e:
            logger.warning(f"Audio processing failed: {e}")
            print("Audio processing exception details:")
            traceback.print_exc()
            f0_1, f0_2 = [], []
            score_mode = "fallback"
            fallback_reason = "音频特征提取失败"
            
        if len(f0_1) < 10 or len(f0_2) < 10:
            score = 0.0
            if score_mode != "fallback":
                score_mode = "fallback"
                fallback_reason = "提取的有效人声过短，未能识别到完整演唱"
        else:
            try:
                # 八度音程归一化：将用户和原唱的 F0 序列整体平移到同一个平均高度
                # 解决男女生音域不同导致的巨大分差
                f0_1_shifted = f0_1 - np.mean(f0_1) + np.mean(f0_2)
                
                # DTW对齐，修复形状问题：必须是2D矩阵
                f0_1_2d = f0_1_shifted.reshape(-1, 1)
                f0_2_2d = f0_2.reshape(-1, 1)
                
                # DTW 距离计算
                D, _ = librosa.sequence.dtw(X=f0_1_2d.T, Y=f0_2_2d.T, metric='euclidean')
                distance = D[-1, -1] / max(len(f0_1), len(f0_2))
                
                # 距离缩放优化：扩大容忍度阈值至 50
                # 加权评分：基础分 40 分，剩下 60 分根据匹配度给出
                match_score = 60 - (distance / 50.0) * 60
                
                if match_score < 0:
                    match_score = 0
                if match_score > 60:
                    match_score = 60
                
                # 总分 = 基础分 + 匹配分
                score = 40 + match_score
                
                # 记录进 debug_info 方便后续排查
                debug_info["dtw_distance"] = float(distance)
            except Exception as e:
                logger.error(f"DTW calculation error: {e}")
                print("DTW calculation exception details:")
                traceback.print_exc()
                score = 0.0
                score_mode = "fallback"
                fallback_reason = "音频波形匹配失败"
                
        score = int(round(score))
        
        # 确保分数在 0-100 之间
        score = max(0, min(100, score))
        
        # 获取歌曲元数据
        song_data = SONG_METADATA.get(song_id)
        if not song_data:
            # 如果没有找到对应的歌曲数据，使用默认兜底文案
            comment = "加油，多听原唱练习"
            if score >= 86:
                comment = "太棒了！音准完美！"
            elif score >= 61:
                comment = "不错哦，继续保持！"
                
            return {
                "score": score,
                "comment": comment,
                "science_copy": None,
                "timbre": None,
                "score_mode": score_mode,
                "fallback_reason": fallback_reason,
                "debug_info": debug_info
            }
            
        # 根据分数匹配对应的话术
        comment = ""
        for c in song_data["comments"]:
            if c["min"] <= score <= c["max"]:
                comment = c["text"]
                break
        
        if not comment:
            comment = song_data["comments"][0]["text"] # 兜底
            
        return {
            "score": score,
            "comment": comment,
            "science_copy": song_data["science_copy"],
            "timbre": song_data["timbre"],
            "score_mode": score_mode,
            "fallback_reason": fallback_reason,
            "debug_info": debug_info
        }
        
    except Exception as e:
        logger.error(f"Score calculation error: {e}")
        print("Score calculation general exception details:")
        traceback.print_exc()
        return {
            "score": 0,
            "comment": "未能识别到有效演唱，请再试一次~",
            "science_copy": None,
            "timbre": None,
            "score_mode": "fallback",
            "fallback_reason": "系统打分异常",
            "debug_info": debug_info
        }

async def call_deepseek_api(score: float, ethnic: str, song: str) -> str:
    """
    调用 DeepSeek API 获取具有云南方言风格的 AI 评语。
    """
    api_key = os.getenv("DEEPSEEK_API_KEY", "sk-c639005134e141a184dbcf264cf8077c")
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    user_text = f"音准{score:.1f}分，{ethnic}歌曲《{song}》"
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": YUNNAN_STYLE_PROMPT},
            {"role": "user", "content": user_text}
        ],
        "temperature": 0.75,
        "max_tokens": 60,
        "top_p": 0.9
    }

    retries = 3
    backoff = 1.0

    async with httpx.AsyncClient() as client:
        for attempt in range(retries):
            try:
                response = await client.post(url, json=payload, headers=headers, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                if "error" in data:
                    raise ValueError(f"API 返回错误: {data['error'].get('code', data['error'])}")
                    
                content = data["choices"][0]["message"]["content"]
                return content.strip(" '\"")
                
            except (httpx.RequestError, httpx.HTTPStatusError, ValueError, KeyError, IndexError) as e:
                logger.warning(f"DeepSeek API 调用失败 (尝试 {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(backoff)
                    backoff *= 2
                else:
                    return "云南的风把点评吹走了，稍后再试哦～"
                    
    return "云南的风把点评吹走了，稍后再试哦～"