"""Package entrypoint for running the Dash app."""
from __future__ import annotations

import argparse

from .utils.config import config
from .dash_app import app


def main() -> None:
    parser = argparse.ArgumentParser(
        prog='vivendi-stock-web',
        description='Run Vivendi Stock Dash web server.'
    )
    parser.add_argument('--host', default=config.DASH_HOST, help='Host to bind (default from DASH_HOST).')
    parser.add_argument(
        '--port',
        type=int,
        default=config.DASH_PORT,
        help='Port to bind (default from DASH_PORT).'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        default=config.DASH_DEBUG,
        help='Enable Dash debug mode.'
    )
    args = parser.parse_args()

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()
