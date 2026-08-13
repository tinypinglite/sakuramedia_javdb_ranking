"""把插件仓库父目录与宿主 src 加入 sys.path，让测试可复用宿主 venv 运行。"""

import sys
from pathlib import Path

PARENT_DIR = Path(__file__).resolve().parents[2]
HOST_SRC = PARENT_DIR / "SakuraMediaBE" / "src"
for path in (PARENT_DIR, HOST_SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
