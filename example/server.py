import asyncio
from aiohttp import web


async def moderate(request):
    body = await request.json()
    messages = body.get("messages", [])
    report = body.get("report")
    print(f"[MODERATE] {len(messages)} messages", end="")
    if report:
        print(f", report: {report[:60]}...")
    else:
        print()
    return web.json_response({"choices": [{"message": {"content": "benign"}}]})


async def health(request):
    return web.json_response({"status": "ok"})


app = web.Application()
app.router.add_post("/moderate", moderate)
app.router.add_get("/health", health)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8080)
