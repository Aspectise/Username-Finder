import asyncio
import aiohttp
import random
import json
from typing import List, Coroutine, Dict, Any
from rgbprint import Color

class Finder:
    def __init__(self) -> None:
        with open("settings.json", "r") as file: settings = json.load(file)
        self.send_to_webhook: bool = settings.get("Webhook").get("Enabled")
        self.webhook: str = settings.get("Webhook").get("Url")
        self.min_length: int = settings.get("Min_length")
        self.max_length: int = settings.get("Max_length")
        self.num_tasks: int = 5
        self.embed_queue: List[Dict[str, Any]] = []

        self.csrf_token: str = None
        self.session: aiohttp.ClientSession = None

    async def get_csrf_token(self) -> None:
        async with self.session.post('https://economy.roblox.com/', ssl=False) as response:
            self.csrf_token: str = response.headers.get('x-csrf-token')

    async def check_username(self, name: str) -> None:
        headers: Dict[str, str] = {'x-csrf-token': self.csrf_token}
        async with self.session.get(
            f"https://auth.roblox.com/v2/usernames/validate?request.username={name}&request.birthday=01%2F01%2F2000&request.context=Signup",
            headers=headers,
            timeout=5,
            ssl=False
        ) as response:
            if response.status == 200:
                result: str = await response.text()
                if "Username is valid" in result:
                    print(f"{Color(0, 255, 0)}Username: {name} is available!{Color(255, 255, 255)}") 
                    with open("users.txt", "a") as file:
                        file.write(name + '\n')
                    if self.send_to_webhook:
                        embed: Dict[str, Any] = {
                            "title": "New Username Found!",
                            "color": 0x00FF00, 
                            "fields": [
                                {"name": "Username", "value": name},
                                {"name": "Register Here!", "value": "[Here!](https://www.roblox.com/signup)"}
                            ]
                        }
                        self.embed_queue.append(embed)
            elif response.status == 403:
                print(f"{Color(255, 255, 0)}CSRF token expired. Getting a new one...{Color(255, 255, 255)}") 
                await self.get_csrf_token() 
            else:
                print(f"{Color(255, 0, 0)}Unexpected response: {response.status}{Color(255, 255, 255)}")

    async def send_webhook(self, embeds: List[Dict[str, Any]]) -> None:
        payload: Dict[str, List[Dict[str, Any]]] = {"embeds": embeds}
        try:
            async with self.session.post(self.webhook, json=payload) as response:
                if response.status != 204:
                    print(f"{Color(255, 0, 0)}Error sending to Discord (status code: {response.status}): {await response.text()}{Color(255, 255, 255)}")
        except Exception as e:
            print(f"{Color(255, 0, 0)}Error sending to Discord: {e}{Color(255, 255, 255)}")

    async def send_embeds_loop(self) -> None:
        while True:
            if len(self.embed_queue) == 10:
                await self.send_webhook(self.embed_queue)
                self.embed_queue = [] 
            else:
                await asyncio.sleep(0.01)

    def generate_name(self) -> str:
        length: int = random.randint(self.min_length, self.max_length)
        characters: str = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
        return ''.join(random.choice(characters) for _ in range(length))

    async def main(self) -> None:
        self.session: aiohttp.ClientSession = aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=None))
        await self.get_csrf_token()

        asyncio.create_task(self.send_embeds_loop(self.session)) 

        while True:
            try:
                tasks: List[Coroutine] = [asyncio.create_task(self.check_username(self.generate_name())) for _ in range(self.num_tasks)]
                await asyncio.gather(*tasks)
            except Exception as e:
                print(f"{Color(255, 0, 0)}An error occurred: {e}{Color(255, 255, 255)}") 
            finally:
                await asyncio.sleep(0.1)  

if __name__ == "__main__":
    sniper: Finder = Finder()
    asyncio.run(sniper.main())
