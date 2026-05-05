import subprocess
import os

class AudioNormalizeError(Exception):
    """音频转码规范化异常"""
    pass

class AudioTranslator:
    @staticmethod
    def normalize_to_wav(input_path: str, output_path: str) -> str:
        """
        强制将输入音频转码为：
        - 采样率: 16000 Hz
        - 声道: 单声道 (1)
        - 编码: 16-bit PCM WAV
        
        如果转码失败，将抛出 AudioNormalizeError。
        """
        if not os.path.exists(input_path):
            raise AudioNormalizeError(f"输入文件不存在: {input_path}")
            
        command = [
            "ffmpeg",
            "-y",               # 覆盖输出文件
            "-i", input_path,   # 输入文件
            "-ar", "16000",     # 采样率 16000
            "-ac", "1",         # 单声道
            "-c:a", "pcm_s16le",# 16-bit PCM 编码
            output_path         # 输出文件
        ]
        
        try:
            result = subprocess.run(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                check=False
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.decode("utf-8", errors="ignore")
                raise AudioNormalizeError(f"FFmpeg 转码失败: {error_msg}")
                
            if not os.path.exists(output_path):
                raise AudioNormalizeError("FFmpeg 运行成功，但未生成输出文件")
                
            return output_path
        except FileNotFoundError:
            raise AudioNormalizeError("未找到 ffmpeg 命令，请确保已安装 FFmpeg")
        except AudioNormalizeError:
            raise
        except Exception as e:
            raise AudioNormalizeError(f"音频标准化过程发生未知异常: {str(e)}")
