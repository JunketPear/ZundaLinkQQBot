# ZundaLinkQQBot

一个模块化的 NoneBot 插件，用于管理 **** 相关流程：账号绑定、机厅上机、机台截图、转发规则与状态查询等。

## 功能特性

- 通过二维码内容绑定 Token
- 按机厅 key 上机并同步规则
- 机台截图获取
- 转发规则列表/查询/更新
- 管理员 @ 代操作（管理员列表控制）
- 配置驱动的机厅与别名

## 运行环境

- NoneBot2
- OneBot v11 适配器
- Python 3.10+

## 配置说明

所有配置文件都在 `config/`：

- `config/config.json`: API 地址、机厅信息、别名、黑名单
- `config/admin.json`: 管理员列表

新增机厅请编辑 `config/config.json` 中的 `arcades`。

## 指令模板

基础

- `/bind <qrcode>`：绑定账号 Token
- `/help`：查看帮助菜单

机厅相关

- `/l<key> <SGWCMAID>`：机厅上机
- `/screenshot<key>` 或 `/peek<key>`：机台截图
- `/add<key>`：同步机厅规则
- `/j<key>`：查询机厅状态

功能

- `/open`：开启全曲解锁
- `/close`：关闭全曲解锁
- `/forward list`：列出已开启规则（会过滤黑名单）
- `/forward <rule>`：查看规则状态和值
- `/forward <rule> <true/false> [value]`：更新规则

管理员

- `/addgroup`：授权群聊（仅群聊内）
- `@user` 后再使用 `/open /close /l<key> /add<key> /forward` 代操作（仅管理员）

## 备注

- 黑名单内的转发规则不可修改。
- 修改配置后请重载插件。
