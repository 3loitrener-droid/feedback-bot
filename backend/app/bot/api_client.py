from __future__ import annotations
import httpx
from app.config import settings


class BotApiClient:
    """HTTP-клиент для взаимодействия бота с FastAPI бэкендом."""

    def __init__(self, token: str):
        self.base_url = settings.api_url
        self.token = token
        self._headers = {"Authorization": f"Bearer {token}"}

    async def get_employees(self) -> list[dict]:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{self.base_url}/api/employees/", headers=self._headers, timeout=10)
            r.raise_for_status()
            return r.json()

    async def get_criteria(self) -> list[dict]:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{self.base_url}/api/criteria/", headers=self._headers, timeout=10)
            r.raise_for_status()
            return r.json()

    async def get_periods(self) -> list[dict]:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{self.base_url}/api/periods/", headers=self._headers, timeout=10)
            r.raise_for_status()
            return r.json()

    async def create_feedback(self, data: dict) -> dict:
        async with httpx.AsyncClient() as client:
            r = await client.post(f"{self.base_url}/api/feedback/", json=data, headers=self._headers, timeout=30)
            r.raise_for_status()
            return r.json()

    async def get_feedback_history(self, employee_id: str, period_id: str | None = None) -> list[dict]:
        params = {"employee_id": employee_id, "limit": 20}
        if period_id:
            params["period_id"] = period_id
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{self.base_url}/api/feedback/", params=params, headers=self._headers, timeout=10)
            r.raise_for_status()
            return r.json()

    async def get_summary(self, employee_id: str, period_id: str) -> dict | None:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self.base_url}/api/summary/",
                params={"employee_id": employee_id, "period_id": period_id},
                headers=self._headers,
                timeout=10,
            )
            if r.status_code == 200:
                return r.json()
            return None

    async def generate_summary(self, employee_id: str, period_id: str) -> dict:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self.base_url}/api/summary/generate",
                params={"employee_id": employee_id, "period_id": period_id},
                headers=self._headers,
                timeout=120,  # LLM может отвечать до 60 сек
            )
            r.raise_for_status()
            return r.json()

    async def analyze_feedback(self, text: str, employee: dict) -> dict:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self.base_url}/api/llm/analyze",
                json={
                    "original_text": text,
                    "employee_name": employee["full_name"],
                    "employee_position": employee.get("position"),
                    "employee_level": employee.get("level"),
                },
                headers=self._headers,
                timeout=60,
            )
            r.raise_for_status()
            return r.json()

    async def auth_by_telegram(self, telegram_id: int) -> dict | None:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self.base_url}/api/auth/telegram-verify",
                params={"telegram_id": telegram_id},
                timeout=10,
            )
            if r.status_code == 200:
                return r.json()
            return None

    async def link_telegram(self, telegram_id: int, email: str) -> dict | None:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self.base_url}/api/auth/telegram-link",
                json={"telegram_id": telegram_id, "email": email},
                timeout=10,
            )
            if r.status_code == 200:
                return r.json()
            return None
