import pytest
import os
import subprocess
import librosa
from utils.audio import AudioTranslator, AudioNormalizeError

@pytest.fixture(scope="module")
def setup_dummy_m4a_files(tmp_path_factory):
    """
    生成 10 个模拟的 m4a 测试文件
    """
    temp_dir = tmp_path_factory.mktemp("test_audio")
    files = []
    
    # 我们使用一段简单的正弦波作为输入音频
    for i in range(10):
        m4a_path = str(temp_dir / f"test_{i}.m4a")
        # 利用 ffmpeg 生成测试音频 (正弦波)
        cmd = [
            "ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=1000:duration=1",
            "-c:a", "aac", "-b:a", "64k", m4a_path
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        files.append(m4a_path)
        
    return temp_dir, files

def test_audio_normalization(setup_dummy_m4a_files):
    temp_dir, m4a_files = setup_dummy_m4a_files
    
    for i, m4a_file in enumerate(m4a_files):
        output_wav = str(temp_dir / f"output_{i}.wav")
        
        # 测试转码是否成功
        result_path = AudioTranslator.normalize_to_wav(m4a_file, output_wav)
        assert os.path.exists(result_path)
        
        # 断言转码后能被 librosa 无警告加载，且采样率严格等于 16 kHz
        try:
            # librosa.load 默认会尝试重新采样，但如果我们指定 sr=None，它会保持原始采样率
            y, sr = librosa.load(result_path, sr=None)
            assert sr == 16000, f"Expected 16000Hz, got {sr}Hz"
            assert len(y.shape) == 1, "Expected mono channel"
        except Exception as e:
            pytest.fail(f"Librosa loading failed: {e}")

def test_audio_normalization_file_not_found():
    with pytest.raises(AudioNormalizeError) as exc_info:
        AudioTranslator.normalize_to_wav("non_existent_file.m4a", "output.wav")
    assert "输入文件不存在" in str(exc_info.value)
