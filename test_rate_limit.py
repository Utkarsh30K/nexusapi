"""
Rate Limiter Test Script

Sends 110 rapid requests to test rate limiting.
Expected: First 100 succeed, last 10 return 429.
"""
import asyncio
import aiohttp
import time

# Configuration
BASE_URL = "http://localhost:8000"
NUM_REQUESTS = 110
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJiYTVmMTg3NC1lMTU5LTQxMmEtYjQ0Mi02N2ZiZGQyNTNkY2UiLCJvcmdfaWQiOiJiZmNiOWE5Ny03NjFmLTQ2NGItYjNmZC0xN2IyZGUyNGQxZmQiLCJyb2xlIjoiYWRtaW4iLCJlbWFpbCI6InV0a2Fyc2hzYXJhc3dhdDMwQGdtYWlsLmNvbSIsImV4cCI6MTc3MjEwNjg4Mn0._JJtUObgq81-eta38CuXJcXWowvz_7A59r_NVgm5BG0"  # Replace with actual token


async def send_request(session, request_num):
    """Send a single GET request to /jobs endpoint (no credits needed)."""
    url = f"{BASE_URL}/api/jobs"
    headers = {
        "Authorization": f"Bearer {TOKEN}"
    }
    
    start = time.time()
    try:
        async with session.get(url, headers=headers) as response:
            duration = time.time() - start
            status = response.status
            retry_after = response.headers.get("Retry-After", None)
            
            if status == 200:
                print(f"Request {request_num:3d}: ✅ SUCCESS ({duration:.3f}s)")
            elif status == 429:
                print(f"Request {request_num:3d}: 🚫 RATE LIMITED ({duration:.3f}s) - Retry-After: {retry_after}")
            else:
                text = await response.text()
                print(f"Request {request_num:3d}: ❌ ERROR {status} - {text[:50]}")
            
            return status, retry_after
    except Exception as e:
        duration = time.time() - start
        print(f"Request {request_num:3d}: 💥 EXCEPTION ({duration:.3f}s) - {e}")
        return None, None


async def main():
    """Run the rate limit test."""
    print("=" * 60)
    print("Rate Limiter Test - Sending 110 requests SEQUENTIALLY")
    print("=" * 60)
    print(f"Expected: 100 succeed, 10 return 429")
    print()
    
    if TOKEN == "YOUR_JWT_TOKEN_HERE":
        print("⚠️  ERROR: Please set your JWT token in the script!")
        print("   Edit test_rate_limit.py and replace TOKEN with your token")
        return
    
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        # Send requests SEQUENTIALLY (one at a time)
        results = []
        for i in range(NUM_REQUESTS):
            result = await send_request(session, i + 1)
            results.append(result)
    
    duration = time.time() - start_time
    
    # Count results
    successes = sum(1 for status, _ in results if status == 200)
    rate_limited = sum(1 for status, _ in results if status == 429)
    errors = sum(1 for status, _ in results if status not in (200, 429, None))
    
    print()
    print("=" * 60)
    print("Results:")
    print(f"  Total requests: {NUM_REQUESTS}")
    print(f"  Successful:     {successes}")
    print(f"  Rate limited:  {rate_limited}")
    print(f"  Errors:        {errors}")
    print(f"  Total time:    {duration:.2f}s")
    print("=" * 60)
    
    # Verify
    if successes == 100 and rate_limited == 10:
        print("✅ DEMO GATE PASSED!")
    else:
        print(f"⚠️  Expected 100 successes and 10 rate limited")


if __name__ == "__main__":
    asyncio.run(main())
