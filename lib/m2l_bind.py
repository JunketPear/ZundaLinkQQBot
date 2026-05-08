from typing import Any, Dict

import httpx

from .config import get_config
from .data_manager import DataManager


async def fetch_token(api_base: str, qrcode: str) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{api_base}/token/get",
            json={"qrcode": qrcode},
        )
        return resp.json()


async def bind_user_token(user_id: str, qrcode: str) -> str:
    ok, result = await bind_user_token_data(user_id, qrcode)
    if ok:
        return "✅ 绑定成功"
    return f"❌ 失败: {result}"


async def bind_user_token_data(user_id: str, qrcode: str) -> tuple[bool, str]:
    if not qrcode:
        return False, "用法: /bind <二维码>"
    cfg = get_config()
    res = await fetch_token(cfg["api_base"], qrcode)
    if res.get("success"):
        token = res["token"]
        bindings = DataManager.get_bindings()
        bindings[str(user_id)] = token
        DataManager.save_bindings(bindings)
        return True, token
    return False, str(res.get("msg", "绑定失败"))
