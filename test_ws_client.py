#!/usr/bin/env python3
"""
Simple WebSocket client test script for rvc2api.
"""
import asyncio
import signal
import sys

import websockets


async def test_websocket(url):
    """Test a WebSocket connection to the specified URL."""
    print(f"Attempting to connect to {url}...")
    try:
        async with websockets.connect(url) as websocket:
            print("Connected! Waiting for messages...")
            # Set up signal handler for Ctrl+C to exit gracefully
            loop = asyncio.get_event_loop()
            loop.add_signal_handler(
                signal.SIGINT, lambda: print("\nReceived exit signal, closing...") or sys.exit(0)
            )

            while True:
                try:
                    message = await websocket.recv()
                    print(f"Received: {message}")
                except websockets.exceptions.ConnectionClosed:
                    print("Connection closed")
                    break
    except Exception as e:
        print(f"Error connecting to WebSocket: {e}")


if __name__ == "__main__":
    url = "ws://localhost:8000/api/ws"
    if len(sys.argv) > 1:
        url = sys.argv[1]

    print("Press Ctrl+C to exit")
    asyncio.run(test_websocket(url))
