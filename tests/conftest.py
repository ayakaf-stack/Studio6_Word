import pytest
from app import app

@pytest.fixture(autouse=True)
def forbid_schema_destruction(monkeypatch):
    """drop_all・create_allが誤って呼ばれても実行させない安全装置"""
    from models.extensions import db

    def _blocked(*args, **kwargs):
        raise RuntimeError("drop_all/create_allはテストコードで使用禁止です")

    monkeypatch.setattr(db, "drop_all", _blocked)
    monkeypatch.setattr(db, "create_all", _blocked)