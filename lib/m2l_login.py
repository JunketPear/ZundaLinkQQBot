from typing import Any, Dict, List, Optional

import httpx

from .config import get_config
from .data_manager import DataManager
from .m2l_bind import bind_user_token_data


def _arcade_conf(arcade_key: str) -> Dict[str, Any]:
    cfg = get_config()
    return cfg["arcades"][arcade_key]


def _normalize_client_ids(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if value is None:
        return []
    text = str(value).strip()
    return [text] if text else []


def _select_client_id(value: Any, index: Optional[int]) -> str:
    ids = _normalize_client_ids(value)
    if not ids:
        return ""
    if index is None:
        return ids[0] if len(ids) == 1 else ""
    if index < 1 or index > len(ids):
        return ""
    return ids[index - 1]


async def register_login(
    api_base: str,
    client_id: str,
    token: str,
    sgwcmaid: str,
) -> Dict[str, Any]:
    payload = {
        "SGWCMAID": sgwcmaid,
        "clientId": client_id,
        "token": token,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{api_base}/aimedb/reg-token",
            json=payload,
            timeout=15,
        )
        return resp.json()


async def login_user(
    user_id: str,
    arcade_key: str,
    sgwcmaid: str,
    index: Optional[int] = None,
) -> str:
    if not sgwcmaid:
        return f"⚠️ 用法: /l{arcade_key} <SGWCMAID>"
    user_token = DataManager.get_bindings().get(str(user_id))
    if not user_token:
        ok, result = await bind_user_token_data(user_id, sgwcmaid)
        if not ok:
            return f"❌ 自动绑定失败: {result}"
        user_token = result
    cfg = get_config()
    conf = _arcade_conf(arcade_key)
    client_id = _select_client_id(conf.get("client_id"), index)
    if not client_id:
        if index is None:
            return f"❌ 该机厅配置了多台机，请使用 /l{arcade_key}1 /l{arcade_key}2 等"
        return "❌ 未配置 client_id"
    res = await register_login(
        cfg["api_base"],
        client_id,
        user_token,
        sgwcmaid,
    )
    if res.get("success"):
        return (
            "✅ 上机成功！\n"
            f"📍 机厅：{conf['name']}\n"
            "🎫 状态：登录指令已下发"
        )
    return f"❌ 上机失败：{res.get('msg', '机台响应异常')}"
