import os
from app import app

# PUBLIC_INTERFACE
def run():
    """Entrypoint to run the Flask application.

    Binds to host 0.0.0.0 and port from the PORT environment variable (default 3001)
    so that the container orchestrator can reach the service externally.
    """
    port = int(os.getenv("PORT", "3001"))
    # Use threaded=True for better responsiveness in simple dev/CI environments.
    app.run(host="0.0.0.0", port=port, threaded=True)

if __name__ == "__main__":
    run()
