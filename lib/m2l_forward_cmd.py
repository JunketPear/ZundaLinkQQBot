from typing import Dict, Set, Tuple

import httpx

from .config import get_config
from .data_manager import DataManager
from .m2l_forward import get_forward_rules, set_forward_rule


PORTRAIT_RULE = "fixUserPortrait"


def _parse_bool(raw: str) -> Tuple[bool, bool]:
    val = raw.strip().lower()
    if val in {"true", "1", "yes", "y", "on"}:
        return True, True
    if val in {"false", "0", "no", "n", "off"}:
        return True, False
    return False, False


def _format_rule_state(rule_name: str, rule_data: Dict) -> str:
    enabled = bool(rule_data.get("enable"))
    state = "开启" if enabled else "关闭"
    value = rule_data.get("value", "")
    return f"{rule_name}: {state} | {value}"


async def _fetch_rules(user_token: str) -> Dict:
    cfg = get_config()
    res = await get_forward_rules(cfg["api_base"], user_token)
    forward_data = res.get("forwardData") or {}
    return forward_data.get("rules", {}) if isinstance(forward_data, dict) else {}


def _blacklist() -> Set[str]:
    cfg = get_config()
    items = cfg.get("blacklist", [])
    return {str(item).strip() for item in items if str(item).strip()}


async def _list_enabled_rules(user_token: str) -> str:
    rules = await _fetch_rules(user_token)
    blocked = _blacklist()
    lines = []
    for name, data in rules.items():
        if name in blocked:
            continue
        if isinstance(data, dict) and data.get("enable"):
            lines.append(_format_rule_state(name, data))
    if not lines:
        return "ℹ️ 当前没有已开启的转发规则。"
    return "\n".join(lines)


async def _query_rule(user_token: str, rule: str) -> str:
    if rule in _blacklist():
        return "该转发规则禁止手动修改，若有需求请联系管理员！"
    rules = await _fetch_rules(user_token)
    data = rules.get(rule)
    if not isinstance(data, dict):
        return f"❌ 未找到规则: {rule}"
    return _format_rule_state(rule, data)


async def update_forward_rule(user_id: str, rule: str, enable_raw: str, value: str) -> str:
    if not rule:
        return "用法: /forward <rule> <true/false> [value]"
    if rule in _blacklist():
        return "该转发规则禁止手动修改，若有需求请联系管理员！"
    ok, enable = _parse_bool(enable_raw)
    if not ok:
        return "❌ true/false 参数无效"
    user_token = DataManager.get_bindings().get(str(user_id))
    if not user_token:
        return "❌ 未绑定！"
    cfg = get_config()
    if value == "":
        rules = await _fetch_rules(user_token)
        current = rules.get(rule, {})
        value = current.get("value", "") if isinstance(current, dict) else ""
    add_res = await set_forward_rule(
        cfg["api_base"],
        user_token,
        rule,
        enable,
        value,
    )
    if add_res.get("success"):
        state = "开启" if enable else "关闭"
        return f"✅ 规则已更新为【{state}】 | {value}"
    return f"❌ 失败: {add_res.get('msg')}"


async def handle_forward_command(user_id: str, args: list[str]) -> str:
    user_token = DataManager.get_bindings().get(str(user_id))
    if not user_token:
        return "❌ 未绑定！"
    if not args:
        return "用法: /forward <rule> <true/false> [value]"
    if args[0].lower() == "list":
        return await _list_enabled_rules(user_token)
    if len(args) == 1:
        return await _query_rule(user_token, args[0])
    rule = args[0]
    enable_raw = args[1]
    value = " ".join(args[2:]) if len(args) > 2 else ""
    return await update_forward_rule(user_id, rule, enable_raw, value)


async def upload_portrait(user_id: str, image_base64: str) -> str:
    """将图片 base64 作为 fixUserPortrait 规则的值上传到服务器"""
    user_token = DataManager.get_bindings().get(str(user_id))
    if not user_token:
        return "❌ 未绑定！"
    cfg = get_config()
    add_res = await set_forward_rule(
        cfg["api_base"],
        user_token,
        PORTRAIT_RULE,
        True,
        image_base64,
        timeout=60,
    )
    if add_res.get("success"):
        return "✅ 头像已上传完毕！"
    return f"❌ 上传失败: {add_res.get('msg')}"
