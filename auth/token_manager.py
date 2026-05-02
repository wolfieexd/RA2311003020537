import httpx
import os
from logging_middleware.logger import Log, set_token
from dotenv import load_dotenv

load_dotenv()

class TokenManager:
    def __init__(self):
        self._token: str = None

    async def authenticate(self):
        payload = {
            "email": os.getenv("EMAIL"),
            "name": os.getenv("NAME"),
            "rollNo": os.getenv("ROLL_NO"),
            "accessCode": os.getenv("ACCESS_CODE"),
            "clientID": os.getenv("CLIENT_ID"),
            "clientSecret": os.getenv("CLIENT_SECRET"),
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://20.207.122.201/evaluation-service/auth",
                json=payload
            )
            if not response.is_success:
                 raise Exception(f"Auth failed (HTTP {response.status_code}): {response.text}")
            data = response.json()
            self._token = data["access_token"]
            # Inject token into logger so it can POST logs
            set_token(self._token)
            Log("backend", "info", "auth", "Authentication successful")
            return self._token

    def get_headers(self) -> dict:
        return {"Authorization": f"Bearer {self._token}"}

    async def get_valid_token(self) -> str:
        if not self._token:
            await self.authenticate()
        return self._token

token_manager = TokenManager()
