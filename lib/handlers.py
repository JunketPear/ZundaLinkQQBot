from nonebot import get_driver, on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, MessageEvent
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

from .admin import resolve_target_user_id
from .config import get_config
from .data_manager import DataManager
from .m2l_add import add_forward_rule
from .m2l_bind import bind_user_token
from .m2l_help import build_help_text
from .m2l_forward_cmd import handle_forward_command
from .m2l_login import login_user
from .m2l_screenshot import is_cq_image, screenshot_message
from .m2l_status import status_message
from .m2l_unlock import toggle_unlock
from .permissions import is_auth


cfg = get_config()
ARCADE_KEYS = set(cfg.get("arcades", {}).keys())


def _normalize_key(raw: str) -> str:
    return raw.strip().lower()


def _alias_map() -> dict:
    alias_to_key = {}
    for key, conf in cfg.get("arcades", {}).items():
        raw = conf.get("nickname", "")
        aliases = [key] + [item.strip() for item in raw.split(",") if item.strip()]
        for alias in aliases:
            alias_to_key[_normalize_key(alias)] = key
    return alias_to_key


ALIASES = _alias_map()


def _arcade_group_allowed(event: MessageEvent, arcade_key: str) -> bool:
    if str(event.user_id) in get_driver().config.superusers:
        return True
    if not isinstance(event, GroupMessageEvent):
        return False
    conf = cfg.get("arcades", {}).get(arcade_key, {})
    groups = conf.get("group_whitelist", [])
    allowed = {str(item).strip() for item in groups if str(item).strip()}
    return str(event.group_id) in allowed


bind = on_command("bind", aliases={"绑定"}, priority=5, rule=is_auth(), block=True)


help_cmd = on_command("help", aliases={"帮助"}, priority=5, rule=is_auth(), block=True)


@help_cmd.handle()
async def _(event: MessageEvent):
    await help_cmd.finish(build_help_text(str(event.user_id)))


@bind.handle()
async def _(event: MessageEvent, arg: Message = CommandArg()):
    qr = arg.extract_plain_text().strip()
    await bind.finish(await bind_user_token(str(event.user_id), qr))


open_unlock = on_command("open", priority=5, rule=is_auth(), block=True)


@open_unlock.handle()
async def _(event: MessageEvent):
    target_user_id = resolve_target_user_id(event)
    await open_unlock.finish(await toggle_unlock(target_user_id, True))


close_unlock = on_command("close", priority=5, rule=is_auth(), block=True)


@close_unlock.handle()
async def _(event: MessageEvent):
    target_user_id = resolve_target_user_id(event)
    await close_unlock.finish(await toggle_unlock(target_user_id, False))


forward_cmd = on_command("forward", priority=5, rule=is_auth(), block=True)


@forward_cmd.handle()
async def _(event: MessageEvent, arg: Message = CommandArg()):
    parts = arg.extract_plain_text().strip().split()
    target_user_id = resolve_target_user_id(event)
    await forward_cmd.finish(await handle_forward_command(target_user_id, parts))


def _register_status_aliases() -> None:
    for alias, key in ALIASES.items():
        status_alias = on_command(f"j{alias}", priority=5, rule=is_auth(), block=True)

        @status_alias.handle()
        async def _(event: MessageEvent, target_key: str = key):
            if not _arcade_group_allowed(event, target_key):
                await status_alias.finish("⚠️ 该机厅仅限指定群聊使用")
            await status_alias.finish(await status_message(target_key))


group_add = on_command("addgroup", permission=SUPERUSER, block=True)


@group_add.handle()
async def _(event: GroupMessageEvent, arg: Message = CommandArg()):
    if not isinstance(event, GroupMessageEvent):
        await group_add.finish("⚠️ 请在群聊中使用该命令")
    gid = arg.extract_plain_text().strip() or str(event.group_id)
    whitelist = DataManager.get_whitelist()
    whitelist.add(gid)
    DataManager.save_whitelist(whitelist)
    await group_add.finish(f"✅ 群聊 {gid} 授权成功")


def _register_arcade_commands(arcade_key: str) -> None:
    conf = cfg.get("arcades", {}).get(arcade_key, {})
    client_ids = conf.get("client_id", [])
    if isinstance(client_ids, list):
        client_id_count = len([str(item).strip() for item in client_ids if str(item).strip()])
    else:
        client_id_count = 1 if str(client_ids).strip() else 0

    login_cmd = on_command(f"l{arcade_key}", priority=5, rule=is_auth(), block=True)

    @login_cmd.handle()
    async def _(event: MessageEvent, arg: Message = CommandArg(), key: str = arcade_key):
        if not _arcade_group_allowed(event, key):
            await login_cmd.finish("⚠️ 该机厅仅限指定群聊使用")
        maid = arg.extract_plain_text().strip()
        target_user_id = resolve_target_user_id(event)
        await login_cmd.finish(await login_user(target_user_id, key, maid))

    if client_id_count > 1:
        for idx in range(1, client_id_count + 1):
            login_idx_cmd = on_command(
                f"l{arcade_key}{idx}",
                priority=5,
                rule=is_auth(),
                block=True,
            )

            @login_idx_cmd.handle()
            async def _(event: MessageEvent, arg: Message = CommandArg(), key: str = arcade_key, index: int = idx):
                if not _arcade_group_allowed(event, key):
                    await login_idx_cmd.finish("⚠️ 该机厅仅限指定群聊使用")
                maid = arg.extract_plain_text().strip()
                target_user_id = resolve_target_user_id(event)
                await login_idx_cmd.finish(
                    await login_user(target_user_id, key, maid, index)
                )

    screenshot_cmd = on_command(
        f"screenshot{arcade_key}",
        aliases={f"peek{arcade_key}"},
        rule=is_auth(),
        block=True,
    )

    @screenshot_cmd.handle()
    async def _(event: MessageEvent, key: str = arcade_key):
        if not _arcade_group_allowed(event, key):
            await screenshot_cmd.finish("⚠️ 该机厅仅限指定群聊使用")
        await screenshot_cmd.send("📸 正在请求机台截图...")
        result = await screenshot_message(key)
        if is_cq_image(result):
            await screenshot_cmd.finish(Message(result))
        else:
            await screenshot_cmd.finish(result)

    add_cmd = on_command(f"add{arcade_key}", priority=5, rule=is_auth(), block=True)

    @add_cmd.handle()
    async def _(event: MessageEvent, key: str = arcade_key):
        if not _arcade_group_allowed(event, key):
            await add_cmd.finish("⚠️ 该机厅仅限指定群聊使用")
        target_user_id = resolve_target_user_id(event)
        await add_cmd.finish(await add_forward_rule(target_user_id, key))


for _key in ARCADE_KEYS:
    _register_arcade_commands(_key)

_register_status_aliases()
