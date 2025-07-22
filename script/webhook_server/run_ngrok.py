#!/usr/bin/env python3
"""
Simple script to run ngrok tunnel for webhook development.
"""

import asyncio
from ngrok_server import NgrokServer

if __name__ == "__main__":
    print("🚀 Starting ngrok tunnel for Flow-State webhooks...")
    print("📋 Make sure your webhook server (main.py) is running on port 8000")
    print()
    
    try:
        server = NgrokServer()
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\n👋 Ngrok tunnel stopped")
    except Exception as e:
        print(f"❌ Error: {e}")