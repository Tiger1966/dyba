import random
import string
from locust import HttpUser, task, between

class RegisterLoginUser(HttpUser):
    wait_time = between(1, 2)  # 用户每次任务后等待1到2秒
    
    @task
    def register_or_login(self):
        # 随机生成一个接近真实分布的手机号，保证有重叠（登录）也有新增（注册）
        prefix = random.choice(["138", "139", "150", "158", "188"])
        suffix = f"{random.randint(0, 99999999):08d}"
        phone = prefix + suffix
        
        # 随机密码
        password = "Password123"
        
        with self.client.post("/api/register", json={"phone": phone, "password": password}, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200 and "data" in data and "user_id" in data["data"]:
                    response.success()
                else:
                    response.failure(f"Unexpected response content: {data}")
            elif response.status_code == 409:
                # 409 是由于并发造成的冲突，理论上正常，但可视为一次失败请求
                response.failure("409 Conflict")
            elif response.status_code == 429:
                # 性能测试中如果遇到限流，可能需要扩大限流阈值或这是预期的
                response.failure("429 Rate Limited")
            else:
                response.failure(f"Status code: {response.status_code}")

# 使用方式:
# locust -f tests/locustfile.py --headless -u 500 -r 50 --run-time 5m --host http://localhost:8000
