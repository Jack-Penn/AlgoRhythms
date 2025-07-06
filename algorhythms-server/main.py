import server
import spotify_auth
from spotify_auth import algorhythms_account
import time
from spotify_api import *

def main():
    try:
        server.start_server()

        # First try to initialize from cache
        if spotify_auth.try_initialize_from_cache():
            print("\nAuthenticated with cached token!")
        else:
            # Fallback to regular login flow
            spotify_auth.prompt_spotify_login()
            print("Waiting for authentication...")
            
            # Wait for token exchange to complete (timeout after 5 minutes)    
            if spotify_auth.wait_for_auth(300):
                print("\nAuthentication flow completed successfully!")
            else:
                print("\nAuthentication timed out. Please try again.")

        # Make API calls here
        print_top_tracks(algorhythms_account)

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