import server
from  spotify_auth import initialize_algorithms_account
from spotify_auth import algorhythms_account
import time
from spotify_api import *

def main():
    try:
        server.start_server()

        initialize_algorithms_account()

        # Make API calls here
        print(algorhythms_account.current_user())

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