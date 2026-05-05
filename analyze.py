import librosa
import numpy as np
import logging
from datetime import datetime
import os

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def predict_timbre(audio_path: str) -> str:
    try:
        start_time = datetime.now()
        filename = os.path.basename(audio_path)
        
        # 加载音频，固定采样率22050，只取前15秒
        y, sr = librosa.load(audio_path, sr=22050, duration=15)
        duration = librosa.get_duration(y=y, sr=sr)
        
        # 1. 频谱质心 (Spectral Centroid)
        centroid_seq = librosa.feature.spectral_centroid(y=y, sr=sr)
        centroid_raw = centroid_seq.mean()
        
        # 归一化质心 (假设 Nyquist 频率为 sr/2)
        nyquist = sr / 2
        centroid_norm = centroid_raw / nyquist
        
        # 频率范围信息
        freq_min = centroid_seq.min()
        freq_max = centroid_seq.max()
        
        # 2. 频谱滚降点 (Spectral Rolloff)
        rolloff_seq = librosa.feature.spectral_rolloff(y=y, sr=sr, roll_percent=0.85)
        rolloff_mean = rolloff_seq.mean()
        
        # 3. 频谱扩展度 (Spectral Bandwidth/Spread)
        bandwidth_seq = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        bandwidth_mean = bandwidth_seq.mean()
        
        # 4. 过零率 (Zero Crossing Rate)
        zcr_seq = librosa.feature.zero_crossing_rate(y)
        zcr_mean = zcr_seq.mean()
        
        # 详细调试日志输出
        logger.info(f"[{start_time.isoformat()}] 文件名: {filename}")
        logger.info(f"    - 音频时长: {duration:.2f} 秒")
        logger.info(f"    - Centroid (原始均值): {centroid_raw:.2f} Hz")
        logger.info(f"    - Centroid (归一化值): {centroid_norm:.4f}")
        logger.info(f"    - Centroid (频率范围): {freq_min:.2f} Hz - {freq_max:.2f} Hz")
        logger.info(f"    - Rolloff (滚降点均值): {rolloff_mean:.2f} Hz")
        logger.info(f"    - Spread (扩展度均值): {bandwidth_mean:.2f} Hz")
        logger.info(f"    - ZCR (过零率均值): {zcr_mean:.4f}")
        
        # 多维度综合评分逻辑
        # 粗犷的声音通常有更多的宽带噪声成分（更高的过零率，更宽的频带）
        # 甜美的声音更集中在基频和谐波上（质心较低，频带较窄）
        
        # 归一化特征 (基于一般经验分布，后续可通过优化脚本更新参数)
        norm_centroid = (centroid_raw - 1500) / 1000
        norm_bandwidth = (bandwidth_mean - 1500) / 1000
        norm_zcr = (zcr_mean - 0.05) / 0.05
        
        # 综合得分 (权重为初步估计值)
        timbre_score = 0.4 * norm_centroid + 0.4 * norm_bandwidth + 0.2 * norm_zcr
        
        logger.info(f"    - 综合音色得分: {timbre_score:.4f}")
        
        # 动态阈值：基于综合得分进行判断，阈值为 0.0
        if timbre_score > 0.0:
            result = "粗犷"
        else:
            result = "甜美"
            
        logger.info(f"    => 最终判定类型: {result}")
        return result
        
    except Exception as e:
        logger.error(f"分析失败: {e}")
        return "中性"
