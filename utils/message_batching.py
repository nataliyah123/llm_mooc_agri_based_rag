import asyncio
from typing import List, Dict, Any
import anthropic
from datetime import datetime, timedelta

class MessageBatcher:
    def __init__(self, api_key: str, batch_size: int = 5, batch_timeout: float = 1.0):
        self.client = anthropic.Client(api_key=api_key)
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.message_queue = asyncio.Queue()
        self.cache = {}
        
    async def add_message(self, system: str, message: str) -> str:
        cache_key = f"{system}:{message}"
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        future = asyncio.Future()
        await self.message_queue.put((system, message, future))
        return await future

    async def process_batch(self):
        while True:
            batch: List[tuple] = []
            try:
                while len(batch) < self.batch_size:
                    try:
                        item = await asyncio.wait_for(
                            self.message_queue.get(),
                            timeout=self.batch_timeout if batch else None
                        )
                        batch.append(item)
                    except asyncio.TimeoutError:
                        break

                if batch:
                    responses = await self._process_messages(batch)
                    for (system, message, future), response in zip(batch, responses):
                        cache_key = f"{system}:{message}"
                        self.cache[cache_key] = response
                        if not future.done():
                            future.set_result(response)

            except Exception as e:
                for _, _, future in batch:
                    if not future.done():
                        future.set_exception(e)

    async def _process_messages(self, batch: List[tuple]) -> List[str]:
        responses = []
        for system, message, _ in batch:
            try:
                response = await self.client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=1024,
                    system=system,
                    messages=[{"role": "user", "content": message}]
                )
                responses.append(response.content[0].text)
            except Exception as e:
                responses.append(str(e))
        return responses

    def start(self):
        asyncio.create_task(self.process_batch())