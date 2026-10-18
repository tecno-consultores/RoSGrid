# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

from __future__ import annotations

import fnmatch
from collections.abc import AsyncGenerator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


class FakePipeline:
    def __init__(self, fake_redis: "FakeAsyncRedis"):
        self.fake_redis = fake_redis
        self.commands: list[Any] = []

    def hset(
        self, name: str, key: str | None = None, value: str | None = None, mapping: dict[str, Any] | None = None
    ) -> "FakePipeline":
        self.commands.append(("hset", (name, key, value, mapping)))
        return self

    def expire(self, name: str, time_sec: int) -> "FakePipeline":
        self.commands.append(("expire", (name, time_sec)))
        return self

    def delete(self, *names: str) -> "FakePipeline":
        self.commands.append(("delete", names))
        return self

    def sadd(self, name: str, *values: Any) -> "FakePipeline":
        self.commands.append(("sadd", (name, values)))
        return self

    def srem(self, name: str, *values: Any) -> "FakePipeline":
        self.commands.append(("srem", (name, values)))
        return self

    def zadd(self, name: str, mapping: dict[Any, float]) -> "FakePipeline":
        self.commands.append(("zadd", (name, mapping)))
        return self

    def zrem(self, name: str, *members: Any) -> "FakePipeline":
        self.commands.append(("zrem", (name, members)))
        return self

    def publish(self, channel: str, message: str) -> "FakePipeline":
        self.commands.append(("publish", (channel, message)))
        return self

    async def execute(self) -> list[Any]:
        results = []
        for cmd, args in self.commands:
            if cmd == "hset":
                name, key, val, mapping = args
                res = await self.fake_redis.hset(name, key=key, value=val, mapping=mapping)
                results.append(res)
            elif cmd == "expire":
                results.append(True)
            elif cmd == "delete":
                for n in args:
                    await self.fake_redis.delete(n)
                results.append(1)
            elif cmd == "sadd":
                name, vals = args
                for v in vals:
                    await self.fake_redis.sadd(name, v)
                results.append(len(vals))
            elif cmd == "srem":
                name, vals = args
                for v in vals:
                    await self.fake_redis.srem(name, v)
                results.append(1)
            elif cmd == "zadd":
                name, m = args
                await self.fake_redis.zadd(name, m)
                results.append(len(m))
            elif cmd == "zrem":
                name, members = args
                for mem in members:
                    await self.fake_redis.zrem(name, mem)
                results.append(1)
            elif cmd == "publish":
                results.append(1)
        self.commands.clear()
        return results


class FakeAsyncRedis:
    def __init__(self) -> None:
        self.strings: dict[str, str] = {}
        self.hashes: dict[str, dict[str, str]] = {}
        self.sets: dict[str, set[str]] = {}
        self.zsets: dict[str, dict[str, float]] = {}

    async def get(self, name: str) -> str | None:
        return self.strings.get(name)

    async def set(
        self,
        name: str,
        value: Any,
        ex: int | None = None,
        px: int | None = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        if nx and name in self.strings:
            return False
        if xx and name not in self.strings:
            return False
        self.strings[name] = str(value)
        return True

    async def hset(
        self,
        name: str,
        key: str | None = None,
        value: str | None = None,
        mapping: dict[str, Any] | None = None,
    ) -> int:
        if name not in self.hashes:
            self.hashes[name] = {}
        count = 0
        if mapping:
            for k, v in mapping.items():
                self.hashes[name][str(k)] = str(v)
                count += 1
        if key is not None and value is not None:
            self.hashes[name][str(key)] = str(value)
            count += 1
        return count

    async def hgetall(self, name: str) -> dict[str, str]:
        return dict(self.hashes.get(name, {}))

    async def delete(self, *names: str) -> int:
        count = 0
        for n in names:
            if n in self.strings:
                del self.strings[n]
                count += 1
            if n in self.hashes:
                del self.hashes[n]
                count += 1
            if n in self.sets:
                del self.sets[n]
                count += 1
            if n in self.zsets:
                del self.zsets[n]
                count += 1
        return count

    async def expire(self, name: str, time_sec: int) -> bool:
        return True

    async def exists(self, *names: str) -> int:
        count = 0
        for n in names:
            if n in self.strings or n in self.hashes or n in self.sets or n in self.zsets:
                count += 1
        return count

    async def sadd(self, name: str, *values: Any) -> int:
        if name not in self.sets:
            self.sets[name] = set()
        c = 0
        for v in values:
            if str(v) not in self.sets[name]:
                self.sets[name].add(str(v))
                c += 1
        return c

    async def srem(self, name: str, *values: Any) -> int:
        if name not in self.sets:
            return 0
        c = 0
        for v in values:
            if str(v) in self.sets[name]:
                self.sets[name].remove(str(v))
                c += 1
        return c

    async def smembers(self, name: str) -> set[str]:
        return set(self.sets.get(name, set()))

    async def scard(self, name: str) -> int:
        return len(self.sets.get(name, set()))

    def pubsub(self) -> Any:
        class FakePubSub:
            async def subscribe(self, *channels: str) -> None:
                pass

            async def unsubscribe(self, *channels: str) -> None:
                pass

            async def get_message(self, *args: Any, **kwargs: Any) -> dict[str, Any] | None:
                return None

            async def close(self) -> None:
                pass

        return FakePubSub()

    async def zadd(self, name: str, mapping: dict[Any, float]) -> int:
        if name not in self.zsets:
            self.zsets[name] = {}
        for k, v in mapping.items():
            self.zsets[name][str(k)] = float(v)
        return len(mapping)

    async def zrem(self, name: str, *members: Any) -> int:
        if name not in self.zsets:
            return 0
        c = 0
        for m in members:
            if str(m) in self.zsets[name]:
                del self.zsets[name][str(m)]
                c += 1
        return c

    async def zrange(self, name: str, start: int, end: int) -> list[str]:
        items = self.zsets.get(name, {})
        sorted_members = sorted(items.keys(), key=lambda k: items[k])
        if end == -1:
            return sorted_members[start:]
        return sorted_members[start : end + 1]

    async def keys(self, pattern: str) -> list[str]:
        all_keys = list(self.strings.keys()) + list(self.hashes.keys()) + list(self.sets.keys()) + list(self.zsets.keys())
        return [k for k in all_keys if fnmatch.fnmatch(k, pattern)]

    async def publish(self, channel: str, message: str) -> int:
        return 1

    async def ping(self) -> bool:
        return True

    def pipeline(self) -> FakePipeline:
        return FakePipeline(self)

    async def aclose(self) -> None:
        self.strings.clear()
        self.hashes.clear()
        self.sets.clear()
        self.zsets.clear()


@pytest.fixture(autouse=True)
def configure_test_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.core.config import settings

    monkeypatch.setattr(settings, "ROSGRID_ENV", "qa_unit")


@pytest.fixture(autouse=True)
def fake_redis(monkeypatch: pytest.MonkeyPatch) -> FakeAsyncRedis:
    fake = FakeAsyncRedis()
    monkeypatch.setattr("src.main.get_redis_client", lambda: fake)
    monkeypatch.setattr("src.redis_layer.client.get_redis_client", lambda: fake)
    monkeypatch.setattr("src.redis_layer.sessions.get_redis_client", lambda: fake)
    monkeypatch.setattr("src.redis_layer.idempotency.get_redis_client", lambda: fake)
    monkeypatch.setattr("src.api.deps.get_redis_client", lambda: fake)
    monkeypatch.setattr("src.api.v1.auth.get_redis_client", lambda: fake)
    monkeypatch.setattr("src.api.v1.sessions.get_redis_client", lambda: fake)
    monkeypatch.setattr("src.api.v1.inventory.get_redis_client", lambda: fake)
    monkeypatch.setattr("src.api.v1.websockets.get_redis_client", lambda: fake)
    monkeypatch.setattr("src.services.telemetry_multiplexer.get_redis_client", lambda: fake)
    return fake


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
