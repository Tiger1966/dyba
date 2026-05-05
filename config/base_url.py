import os
from dotenv import load_dotenv

load_dotenv()

def get_base_url() -> str:
    """
    获取全局 Base URL，优先从环境变量 PUBLIC_BASE_URL 读取，
    未配置时使用默认值。
    """
    return os.getenv("PUBLIC_BASE_URL", "http://139.199.66.118:8000")
