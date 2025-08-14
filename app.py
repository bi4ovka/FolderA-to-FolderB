import asyncio
from pathlib import Path
import time

class RateLimiterWorker:
    def __init__(self, max_per_sec: int):
        self.queue = asyncio.Queue()
        self.max_per_sec = max_per_sec
        self.call_times = []

    async def start(self):
        while True:
            func, args, kwargs, future = await self.queue.get()

            #лимит по времени
            now = time.monotonic()
            self.call_times = [t for t in self.call_times if now - t < 1]
            if len(self.call_times) >= self.max_per_sec:
                await asyncio.sleep(1 - (now - self.call_times[0]))
                now = time.monotonic()
                self.call_times = [t for t in self.call_times if now - t < 1]

            try:
                result = await func(*args, **kwargs)
                future.set_result(result)
            except Exception as e:
                future.set_exception(e)

            self.call_times.append(time.monotonic())
            self.queue.task_done()

    async def submit(self, func, *args, **kwargs):
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        await self.queue.put((func, args, kwargs, future))
        return await future

async def list_folders(path: Path):
    await asyncio.sleep(0)  # заглушка 
    return [p.name for p in path.iterdir() if p.is_dir()]

async def create_folder(parent_path: Path, folder_name: str):
    await asyncio.sleep(0)  # заглушка
    new_path = parent_path / folder_name
    new_path.mkdir(exist_ok=True)
    return new_path

#Копирование структуры по уровням
async def copy_structure_by_levels(src_root: Path, dst_root: Path, worker: RateLimiterWorker):
    current_level = [(src_root, dst_root)]

    while current_level:
        next_level = []

        for src_parent, dst_parent in current_level:
            subfolders = await list_folders(src_parent)
            create_tasks = [
                worker.submit(create_folder, dst_parent, name)
                for name in subfolders
            ]
            created_folders = await asyncio.gather(*create_tasks)

            for name, dst_path in zip(subfolders, created_folders):
                src_path = src_parent / name
                next_level.append((src_path, dst_path))

        current_level = next_level

async def main():
    src = Path("A")
    dst = Path("B")
    dst.mkdir(exist_ok=True)

    worker = RateLimiterWorker(max_per_sec=10)
    asyncio.create_task(worker.start())

    await copy_structure_by_levels(src, dst, worker)

if __name__ == "__main__":

    asyncio.run(main())
