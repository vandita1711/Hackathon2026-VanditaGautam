import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
WORKSPACE_ROOT = ROOT.parent
local_site_packages = ROOT / ".local" / "lib" / "python3.13" / "site-packages"
venv_site_packages = WORKSPACE_ROOT / ".venv" / "Lib" / "site-packages"

if local_site_packages.exists():
    sys.path.insert(0, str(local_site_packages))

if venv_site_packages.exists():
    sys.path.insert(0, str(venv_site_packages))
