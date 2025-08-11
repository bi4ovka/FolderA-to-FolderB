import asyncio
import time
from pathlib import Path
from collections import deque

async def list_folders(path: Path):
    await asyncio.sleep(0) 
    return [p.name for p in path.iterdir() if p.is_dir()]

async def create_folder(parent: Path, name: str):
    await asyncio.sleep(0)
    new_path = parent / name
    new_path.mkdir(exist_ok=True)
    return new_path

class RateLimiter:
    def __init__(self, max_per_sec: int):
        self.max_per_sec = max_per_sec
        self.calls = deque()

    async def wait(self):
        now = time.monotonic()
        while len(self.calls) >= self.max_per_sec:
            oldest = self.calls[0]
            wait_time = 1 - (now - oldest)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            else:
                self.calls.popleft()
            now = time.monotonic()
        self.calls.append(now)

async def copy_structure(src: Path, dst: Path, limiter: RateLimiter):
    subfolders = await list_folders(src)

    tasks = []
    for name in subfolders:
        await limiter.wait()      
        new_dst = await create_folder(dst, name) 
        tasks.append(copy_structure(src / name, new_dst, limiter))
    for t in tasks:
        await t

async def main():
    src = Path("A")
    dst = Path("B")
    dst.mkdir(exist_ok=True)

    limiter = RateLimiter(10)
    await copy_structure(src, dst, limiter)

if __name__ == "__main__":
    asyncio.run(main())
