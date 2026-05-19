import json
import os
import asyncio
import aiohttp
import time

DATA_FILE = "data/data.json"
API_URL = os.getenv("API_URL", "http://localhost:8080/moderate")
NUM_CONCURRENT = int(os.getenv("NUM_CONCURRENT", "3"))
REQUESTS_PER_SECOND = int(os.getenv("REQUESTS_PER_SECOND", "2"))


class RateLimiter:
    """Simple token bucket rate limiter."""

    def __init__(self, rate: float):
        self.rate = rate  # requests per second
        self.min_interval = 1.0 / rate
        self.last_request_time = 0.0
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_request_time
            if elapsed < self.min_interval:
                wait_time = self.min_interval - elapsed
                await asyncio.sleep(wait_time)
            self.last_request_time = time.monotonic()


async def process_sample(sample, rate_limiter: RateLimiter, session: aiohttp.ClientSession, results: list, idx: int):
    """Process a single sample incrementally, stopping on 'malicious'."""
    label = sample["label"]
    messages = sample["sample"]["messages"]
    total_msgs = len(messages)
    report = sample["sample"].get("report")

    api_messages = []
    stopped_early = False
    last_response = ""

    for j, msg in enumerate(messages):
        api_messages.append({"role": msg["role"], "content": msg["content"]})

        # Rate limit
        await rate_limiter.acquire()

        # Build payload: messages are always sent; report is optional and included only on the last message
        payload = {"messages": api_messages}
        if report is not None and j == total_msgs - 1:
            payload["report"] = report

        try:
            async with session.post(API_URL, json=payload) as resp:
                result = await resp.json()
        except Exception as e:
            last_response = f"error: {e}"
            print(f"\n  [{idx}] [{j + 1}/{total_msgs}] ERROR: {e}")
            continue

        if "choices" in result and result["choices"]:
            last_response = result["choices"][0].get("message", {}).get("content", "").strip().lower()
        else:
            last_response = str(result).lower()

        preview = msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]

        print(f"  [{idx}] [{j + 1}/{total_msgs}] [{msg['role']}] {preview} → {last_response}")

        if last_response == "malicious":
            stopped_early = True
            print(f"  [{idx}] [STOPPED EARLY — malicious]")
            break

    status = "✓" if last_response == label else "✗"
    results[idx] = {
        "label": label,
        "prediction": last_response,
        "correct": last_response == label,
        "stopped_early": stopped_early,
    }
    print(f"  [{idx}] Expected: {label} | Got: {last_response} | {status}")


async def main():
    async with aiohttp.ClientSession() as session:
        with open(DATA_FILE, "r") as f:
            samples = json.load(f)

        total = len(samples)
        results = [None] * total
        rate_limiter = RateLimiter(REQUESTS_PER_SECOND)

        print(f"\nAPI URL: {API_URL}")
        print(f"Concurrent conversations: {NUM_CONCURRENT}")
        print(f"Rate limit: {REQUESTS_PER_SECOND} requests/second")
        print(f"Total samples: {total}\n")

        sem = asyncio.Semaphore(NUM_CONCURRENT)

        async def worker(idx, sample):
            async with sem:
                await process_sample(sample, rate_limiter, session, results, idx)

        tasks = [asyncio.create_task(worker(i, sample)) for i, sample in enumerate(samples)]
        await asyncio.gather(*tasks)

        # Print summary
        correct = sum(1 for r in results if r and r["correct"])
        incorrect = total - correct
        stopped = sum(1 for r in results if r and r["stopped_early"])

        print(f"\n{'=' * 60}")
        print("RESULTS")
        print(f"{'=' * 60}")
        print(f"Total samples: {total}")
        print(f"Stopped early (malicious): {stopped}")
        print(f"Correct: {correct}/{total}")
        print(f"Incorrect: {incorrect}/{total}")
        if total > 0:
            print(f"Accuracy: {correct / total * 100:.1f}%")


if __name__ == "__main__":
    asyncio.run(main())
