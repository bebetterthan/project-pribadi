"""
Simple SSE Test - Test if EventSourceResponse works independently
"""
import asyncio
from fastapi import FastAPI
from sse_starlette.sse import EventSourceResponse
import json

app = FastAPI()

@app.get("/test-sse")
async def test_sse():
    """Simple SSE test endpoint"""
    async def event_generator():
        # Send 3 simple messages
        for i in range(3):
            event_data = {
                "type": "test",
                "content": f"Test message {i+1}",
                "timestamp": "2025-01-08T00:00:00"
            }
            yield json.dumps(event_data)
            await asyncio.sleep(0.5)
    
    return EventSourceResponse(event_generator())

if __name__ == "__main__":
    import uvicorn
    print("🧪 Starting SSE test server on http://localhost:9999")
    print("📡 Test endpoint: http://localhost:9999/test-sse")
    print("🔧 Use: curl -N http://localhost:9999/test-sse")
    uvicorn.run(app, host="0.0.0.0", port=9999)

