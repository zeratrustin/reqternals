import asyncio
import json
import sys
import time
from playwright.async_api import async_playwright

async def run(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            extra_http_headers={
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        page = await context.new_page()

        requests_data = []
        console_data = []
        
        start_times = {}
        async def handle_request(request):
            start_times[request] = time.perf_counter()

        async def handle_response(response):
            duration = "-"

            end_time = time.perf_counter()
            start_time = start_times.get(response.request)

            if start_time:
                duration_ms = (end_time - start_time) * 1000
                duration = f"{duration_ms:.2f}ms"
            
            requests_data.append({
                "url": response.url,
                "status": response.status if response.status else '-',
                "duration": duration,
                "req_headers": json.dumps(response.request.headers),
                "res_headers": json.dumps(response.headers)
            })

        page.on("request", handle_request)
        page.on("response", handle_response)
        page.on("console", lambda msg: console_data.append({
            "time": time.strftime("%H:%M:%S"),
            "type": msg.type,
            "text": msg.text,
            "origin": f"{msg.location.get('url', 'unknown')}:{msg.location.get('lineNumber', 0)}"
        }))

        try:
            await page.goto(url, wait_until="load", timeout=60000)

            await asyncio.sleep(5)
        except Exception as e:
            print(f"Error: {e}")

        print("\n== Requests: ==")
        print('Status Duration URL Req_headers Res_headers')
        for r in requests_data:
            print(f"{r['status']} {r['duration']} {r['url']} {r['req_headers']} {r['res_headers']}")

        print("\n== Console messages: ==")
        for c in console_data:
            print(f"{c['time']} {c['type'].upper()} {c['text']} ({c['origin']})")

        await browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: reqternal <url>")
    else:
        target_url = sys.argv[1]
        if not target_url.startswith("http"):
            target_url = "https://" + target_url
        asyncio.run(run(target_url))
