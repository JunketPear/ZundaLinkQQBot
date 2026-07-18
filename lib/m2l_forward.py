from typing import Any, Dict

import httpx


async def get_forward_rules(api_base: str, token: str) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{api_base}/forward/get",
            json={"token": token},
            timeout=10,
        )
        return resp.json()


async def set_forward_rule(
    api_base: str,
    token: str,
    rule: str,
    enable: bool,
    value: str,
    timeout: float = 10,
) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{api_base}/forward/add",
            json={
                "token": token,
                "rule": rule,
                "enable": enable,
                "value": value,
            },
            timeout=timeout,
        )
        return resp.json()
