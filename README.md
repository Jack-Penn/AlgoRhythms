# AlgoRhythms

> **Note:** This app requires a personal Spotify Developer application for API access. Currently, user access is limited to accounts manually whitelisted in the developer dashboard because the app is still in development mode.

## Setup

### 1. Create a Spotify Developer App

1.  Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) and log in with your Spotify account.
2.  Click the **"Create app"** button.
3.  Enter an App Name (e.g., "AlgoRhythms") and a description.
4.  Under **Redirect URIs**, add the following:
    ```
    http://[::1]:5173/login/callback
    http://127.0.0.1:8000/server_auth_callback
    ```
5.  Enable the **Web API** and the **Web Playback SDK**.
6.  Agree to the Terms of Service and click **"Save"**.

### 2. Configure Environment Variables

1.  After saving, copy the **Client ID** and **Client Secret** from your app's dashboard.
2.  In the `algorhythms-server` directory, create a file named `secrets.env` with the following content:
    ```env
    SPOTIFY_CLIENT_ID=[Your Spotify Client ID]
    SPOTIFY_CLIENT_SECRET=[Your Spotify Client Secret]
    GEMINI_API_KEY=AIzaSyDyQx1y3xza5Nv1LCz5YxYXoDS9Y9Pbu_g
    ```
3.  In the `algorhythms-client` directory, create a file named `.env` with the following content:
    ```env
    VITE_SPOTIFY_CLIENT_ID=[Your Spotify Client ID]
    ```

## Installation

### Server (Python)

The server uses Python `3.13.5`.

1.  Navigate to the `algorhythms-server` directory.
2.  Create and activate a virtual environment.
3.  Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

### Client (Node.js)

The client uses Node.js `23.5.0`.

1.  Navigate to the `algorhythms-client` directory.
2.  Install the dependencies:
    ```bash
    npm install
    ```

## Running the Application

### 1. Start the Server

1.  From within the `algorhythms-server` directory (with the virtual environment activated), run:
    ```bash
    python main.py
    ```
2.  Your browser may open, prompting you to log in with a Spotify account. This is for server-side authentication and guest login support.

### 2. Start the Client

1.  Open a new terminal.
2.  Navigate to the `algorhythms-client` directory and run:
    ```bash
    npm run dev
    ```
3.  The terminal will display a local URL, typically `http://localhost:5173/`. Open this link in Google Chrome.

If everything is set up correctly, you should now be able to log in to the application and create a playlist.
