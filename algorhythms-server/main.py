import signal
import server
import spotify_auth
import time


def main():
    try:
        server.start_server()

        spotify_auth.prompt_spotify_login()
        print("Waiting for authentication...")
        
        # Wait for token exchange to complete (timeout after 5 minutes)    
        if spotify_auth.wait_for_auth(300):
            print("\nAuthentication flow completed successfully!")
        else:
            print("\nAuthentication timed out. Please try again.")
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
            print("Shutting down server...")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
    finally:
        server.stop_server()
        print("Clean shutdown complete")


if __name__ == "__main__":
    main()