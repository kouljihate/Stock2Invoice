import os
import sys
from dotenv import load_dotenv

load_dotenv()

from app import app
from app.core.utils.helpers import error_context


def _main():
    app.run(
        host=os.getenv('HOST', '127.0.0.1'),
        port=int(os.getenv('PORT', 5002)),
        # The interactive debugger is a remote-code-execution surface: it is
        # opt-in via FLASK_DEBUG=1, never implied by FLASK_ENV.
        debug=os.getenv('FLASK_DEBUG', '0').strip().lower() in ('1', 'true', 'yes'),
    )


if __name__ == '__main__':
    try:
        _main()
    except KeyboardInterrupt:
        print(f"\n[APP STOPPED] Application terminated by user (Ctrl+C). {error_context()}")
        sys.exit(0)
    except Exception as e:
        print(f"[FATAL] {error_context(e)}")
        sys.exit(1)
