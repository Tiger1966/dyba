import re
from pydantic import BaseModel, Field, field_validator

class UserRegister(BaseModel):
    phone: str = Field(
        ..., 
        description="手机号（11位）",
        pattern=r"^1[3-9]\d{9}$"
    )
    password: str = Field(
        ..., 
        min_length=8, 
        max_length=32, 
        description="密码（8-32位，必须包含字母与数字）"
    )

    @field_validator("password")
    def validate_password_complexity(cls, v):
        if not re.search(r"[a-zA-Z]", v):
            raise ValueError("密码必须包含字母")
        if not re.search(r"\d", v):
            raise ValueError("密码必须包含数字")
        return v

class UserRegisterData(BaseModel):
    user_id: int

class UserRegisterResponse(BaseModel):
    code: int = 200
    msg: str = "注册/登录成功"
    data: UserRegisterData
