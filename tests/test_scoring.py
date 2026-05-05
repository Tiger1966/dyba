import pytest
import httpx
from unittest.mock import patch, MagicMock
from scoring import call_deepseek_api

@pytest.mark.asyncio
@patch("scoring.httpx.AsyncClient.post")
async def test_call_deepseek_api_success(mock_post):
    """
    测试正常情况下的 API 调用返回值
    """
    # 模拟成功的 httpx 响应
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": '"哎哟喂，唱得太板扎了！"'
                }
            }
        ]
    }
    mock_post.return_value = mock_response
    
    result = await call_deepseek_api(85.5, "傣族", "小河淌水")
    
    assert result == "哎哟喂，唱得太板扎了！"
    
    # 验证请求体参数
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert "https://api.deepseek.com/v1/chat/completions" in args[0]
    payload = kwargs["json"]
    assert payload["temperature"] == 0.75
    assert payload["max_tokens"] == 60
    assert payload["top_p"] == 0.9
    assert payload["messages"][0]["role"] == "system"
    assert payload["messages"][1]["role"] == "user"
    assert payload["messages"][1]["content"] == "音准85.5分，傣族歌曲《小河淌水》"
    
    # 验证 Header
    assert "Authorization" in kwargs["headers"]
    assert "Bearer sk-c639005134e141a184dbcf264cf8077c" in kwargs["headers"]["Authorization"]

@pytest.mark.asyncio
@patch("scoring.httpx.AsyncClient.post")
@patch("scoring.asyncio.sleep")
async def test_call_deepseek_api_retry_and_fallback(mock_sleep, mock_post, caplog):
    """
    测试发生网络异常时，是否会重试3次并返回降级文案，且记录日志
    """
    # 模拟抛出 RequestError
    mock_post.side_effect = httpx.RequestError("Network Connection Failed")
    
    result = await call_deepseek_api(70.0, "彝族", "月亮出来亮汪汪")
    
    # 断言重试了 3 次
    assert mock_post.call_count == 3
    # 断言睡眠退避策略
    assert mock_sleep.call_count == 2
    mock_sleep.assert_any_call(1.0)
    mock_sleep.assert_any_call(2.0)
    
    # 断言返回了降级文案
    assert result == "云南的风把点评吹走了，稍后再试哦～"
    
    # 断言打出了警告日志
    assert "DeepSeek API 调用失败 (尝试 1/3)" in caplog.text
    assert "DeepSeek API 调用失败 (尝试 3/3)" in caplog.text
