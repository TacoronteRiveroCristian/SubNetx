"""Script to run the SubNetx VPN Metrics API server."""

import uvicorn

from vpn.metrics.api.main import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,  # Enable auto-reload for development
    )
