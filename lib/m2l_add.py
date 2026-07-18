from .config import get_config
from .data_manager import DataManager
from .m2l_forward import get_forward_rules, set_forward_rule
from .utils import mask_key


def _arcade_conf(arcade_key: str) -> dict:
    cfg = get_config()
    return cfg["arcades"][arcade_key]


async def add_forward_rule(user_id: str, arcade_key: str) -> str:
    user_token = DataManager.get_bindings().get(str(user_id))
    if not user_token:
        return "❌ 未绑定！"
    cfg = get_config()
    conf = _arcade_conf(arcade_key)
    target_val = conf["public_key"]
    res = await get_forward_rules(cfg["api_base"], user_token)
    forward_data = res.get("forwardData") or {}
    rules = forward_data.get("rules", {}) if isinstance(forward_data, dict) else {}
    password_rule = rules.get("fixSpecialClientPassword", {})
    old_val = password_rule.get("value", "") if isinstance(password_rule, dict) else ""
    current_keys = [k.strip() for k in str(old_val).split(",") if k.strip()]
    if target_val in current_keys:
        return "✅ 规则已存在。\n" + f"列表: {','.join([mask_key(k) for k in current_keys])}"
    current_keys.append(target_val)
    new_val = ",".join(current_keys)
    add_res = await set_forward_rule(
        cfg["api_base"],
        user_token,
        "fixSpecialClientPassword",
        True,
        new_val,
    )
    if add_res.get("success"):
        return (
            "✅ 规则同步成功！\n"
            f"📍 机厅: {conf['name']}\n"
            f"📝 列表: {','.join([mask_key(k) for k in current_keys])}"
        )
    return f"❌ 写入失败: {add_res.get('msg')}"
