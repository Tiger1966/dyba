import sys
import os
from fastapi import FastAPI

# mock modules to avoid dependencies
class MockRouter:
    def post(self, *args, **kwargs): return lambda f: f

class APIRouter:
    def __init__(self):
        self.routes = []
    def post(self, path, **kwargs):
        def decorator(func):
            self.routes.append(path)
            return func
        return decorator

sys.modules['fastapi'] = type('fastapi', (), {'APIRouter': APIRouter, 'UploadFile': None, 'File': lambda *a,**kw: None, 'Depends': None, 'HTTPException': Exception, 'FastAPI': FastAPI})
