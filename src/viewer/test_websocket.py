#!/usr/bin/env python3
"""
Simple WebSocket test client to verify viewer WebSocket server is working.
"""

import asyncio
import websockets
import json
import sys

async def test_connection(host='localhost', port=8081):
    """Test WebSocket connection to viewer."""
    url = f'ws://{host}:{port}'

    print(f"Testing WebSocket connection to {url}")
    print("=" * 60)

    try:
        async with websockets.connect(url) as websocket:
            print(f"✓ Connected to {url}")

            # Send a test action
            test_message = {
                'type': 'action',
                'action': 'test'
            }
            await websocket.send(json.dumps(test_message))
            print(f"✓ Sent test message: {test_message}")

            # Wait for a few messages
            print("\nWaiting for messages from server...")
            message_count = 0

            async for message in websocket:
                try:
                    data = json.loads(message)
                    msg_type = data.get('type')

                    if msg_type == 'frame':
                        print(f"  [{message_count}] Received frame (size: {len(data.get('data', ''))} bytes)")
                    elif msg_type == 'status':
                        print(f"  [{message_count}] Received status: {data}")
                    else:
                        print(f"  [{message_count}] Received: {msg_type}")

                    message_count += 1

                    # Stop after 10 messages
                    if message_count >= 10:
                        print(f"\n✓ Test successful! Received {message_count} messages")
                        break

                except json.JSONDecodeError:
                    print(f"  [{message_count}] Received non-JSON message")
                    message_count += 1

    except ConnectionRefusedError:
        print(f"✗ Connection refused. Is the viewer running?")
        print(f"  Make sure to start the viewer with: python3 src/viewer/run.py")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Test WebSocket connection to viewer")
    parser.add_argument('--host', default='localhost', help='WebSocket server host')
    parser.add_argument('--port', type=int, default=8081, help='WebSocket server port')

    args = parser.parse_args()

    # Run the test
    success = asyncio.run(test_connection(args.host, args.port))

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
