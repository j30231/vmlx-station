from __future__ import annotations

import argparse

import uvicorn

from .app import create_app
from .config import AppPaths, load_config


def main() -> None:
    paths = AppPaths.default()
    config = load_config(paths)

    parser = argparse.ArgumentParser(description="Run the vMLX Station daemon")
    parser.add_argument("--host", default=config.control_api.host)
    parser.add_argument("--port", type=int, default=config.control_api.port)
    args = parser.parse_args()

    uvicorn.run(create_app(), host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()

