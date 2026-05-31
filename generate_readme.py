from pathlib import Path
from datetime import datetime

repo = "USERNAME/REPO"

# =========================
# LINKS SAFE LOAD
# =========================
def load(path, fallback):
    p = Path(path)
    return p.read_text(encoding="utf-8").strip() if p.exists() else fallback

vitrina_url = load(
    "VITRINA_URL.txt",
    f"https://gitverse.ru/{repo}/raw/main/playlists/vitrina/vitrina.m3u"
)

rutube_url = load(
    "RUTUBE_URL.txt",
    f"https://gitverse.ru/{repo}/raw/main/playlists/rutube/rutube.m3u"
)

timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# =========================
# README (NO BROKEN TRIPLE QUOTES ISSUES)
# =========================
readme = (
    "# 🚀 IPTV Ultimate Sniffer\n\n"
    "Автоматическая система сбора IPTV потоков.\n\n"
    "## 📡 Плейлисты\n\n"
    "| Источник | Ссылка |\n"
    "|---|---|\n"
    f"| 🎬 Vitrina TV | {vitrina_url} |\n"
    f"| 📺 RuTube Live | {rutube_url} |\n\n"
    "## ⚙️ Запуск вручную\n\n"
    "RuTube:\n"
    "```\n"
    "git commit --allow-empty -m \"[rutube] run\"\n"
    "git push\n"
    "```\n\n"
    "Vitrina:\n"
    "```\n"
    "git commit --allow-empty -m \"[vitrina] run\"\n"
    "git push\n"
    "```\n\n"
    f"## 📊 Обновлено\n\n{timestamp}\n"
)

# =========================
# WRITE FILE
# =========================
Path("README.md").write_text(readme, encoding="utf-8")

print("README OK")