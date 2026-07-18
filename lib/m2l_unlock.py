from .config import get_config
from .data_manager import DataManager
from .m2l_forward import get_forward_rules, set_forward_rule


def _status_name(target_state: bool) -> str:
    return "开启" if target_state else "关闭"


async def toggle_unlock(user_id: str, target_state: bool) -> str:
    user_token = DataManager.get_bindings().get(str(user_id))
    if not user_token:
        return "❌ 未绑定！"
    cfg = get_config()
    res = await get_forward_rules(cfg["api_base"], user_token)
    forward_data = res.get("forwardData") or {}
    rules = forward_data.get("rules", {}) if isinstance(forward_data, dict) else {}
    music_rule = rules.get("fixUnlockALLMusic", {})
    status_name = _status_name(target_state)
    if music_rule.get("enable") is target_state:
        return f"ℹ️ 已经是【{status_name}】状态。"
    add_res = await set_forward_rule(
        cfg["api_base"],
        user_token,
        "fixUnlockALLMusic",
        target_state,
        music_rule.get("value", ""),
    )
    if add_res.get("success"):
        return f"✅ 全曲解锁已【{status_name}】"
    return f"❌ 失败: {add_res.get('msg')}"
