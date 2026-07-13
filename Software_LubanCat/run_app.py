from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from voice_fault_diagnosis.runtime_checks import (
    configure_lubancat_environment,
    desktop_dependency_errors,
    format_desktop_dependency_error,
)


configure_lubancat_environment(ROOT)
_dependency_errors = desktop_dependency_errors()
if _dependency_errors:
    print(format_desktop_dependency_error(_dependency_errors, ROOT), file=sys.stderr)
    raise SystemExit(2)

from voice_fault_diagnosis.app.main_window import main


if __name__ == "__main__":
    raise SystemExit(main())
