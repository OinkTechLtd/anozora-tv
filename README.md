<div align="center">
  
# 🎬 ANOZORA TV

### *"Because your playlist deserves a first-class ticket to the aether"*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![Maintained](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/OinkTechLtd/anozora-tv/graphs/commit-activity)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

</div>

---

## 🚀 **What is this?**

**Anozora TV** is a smart, automated IPTV playlist generator that scrapes, filters and serves `.m3u` streams from **Rutube**, **Vitrina** and more.  
Think of it as your personal TV guide that never sleeps — always fresh, always ready to stream.

```python
# One line to rule them all
curl -s https://raw.githubusercontent.com/OinkTechLtd/anozora-tv/main/playlists/rutube.m3u | vlc -

✨ Features that slap
Feature	Description
🤖 Auto‑updating	Playlists refresh automatically — you do nothing
🧹 Clean streams	Filtered vs raw dumps: pick your poison
📦 Zero bloat	No dependencies, no install — just raw M3U files
🔗 Plug & play	Works with VLC, OTT Navigator, IPTV Smarters, Kodi

📁 Project
anozora-tv/
├── 📂 playlists/
│   ├── 🟠 rutube.m3u          # Clean Rutube streams
│   ├── 🟢 vitrina.m3u         # Clean Vitrina streams
│   └── 🔴 vitrina_all.m3u     # Raw Vitrina dump (all channels)
├── ⚙️ depo.yaml               # Source config (add your own!)
├── 🐍 generate_readme.py      # README generator script
└── 🤖 .github/                # CI/CD automation

⚡ Quick start (3 seconds)
Copy this M3U link into any IPTV player:

http
https://raw.githubusercontent.com/OinkTechLtd/anozora-tv/main/playlists/rutube.m3u
Or clone & regenerate manually:

bash
git clone https://github.com/OinkTechLtd/anozora-tv.git
cd anozora-tv
python3 generate_readme.py   # 👈 refreshes playlists + this README
Done. Go watch some streams.

🧪 Tested on
Player	Status
VLC	✅ Full support
OTT Navigator	✅ Full support
IPTV Smarters Pro	✅ Full support
Kodi (PVR IPTV Simple)	✅ Works
MPV	✅ Works with --playlist
🛠️ I want MOAR (custom sources)
Edit depo.yaml and add any URL that returns an M3U playlist:


📜 License
MIT – do whatever you want, just don't sue us.


Copyright (c) 2025 OinkTechLtd

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files...
