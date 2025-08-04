import asyncio
import server
from  spotify_auth import get_spotify_clients
import time

def main():
    try:
        asyncio.run(get_spotify_clients())
        server.start_server()

        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down server...")
    finally:
        server.stop_server()
        print("Clean shutdown complete")

if __name__ == "__main__":
    main()