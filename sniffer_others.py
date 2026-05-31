#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RUTUBE SNIFFER -- TRIPLE METHOD v6
Method 1: Network response interception (Playwright)
Method 2: JS injection -- extract player.config and window objects
Method 3: Direct API call to Rutube video info endpoint
+ STRICT ad filtering
+ Channel validation by video_id
+ Collects ALL valid streams per channel
"""

import asyncio, os, time, json, re
from datetime import datetime
from urllib.parse import urlparse
from playwright.async_api import async_playwright

OUTPUT_DIR   = "playlists/rutube"
WAIT_MS      = 12000
NAV_TIMEOUT  = 30000
API_TIMEOUT  = 15000

CHANNELS = [
    ("1plus-minus16",    "1+-16 (16+-)",    "99d4597cea881a27cf7dd6e65a74dade"),
    ("2x2",        "2x2",          "392b4686b770bae2da6bf5ac4574add5"),
    ("ru-tv",      "RU TV",        "b1eb8e90d7e636677b3eb73b4fcbb717"),
    ("muztv",      "MUZ TV",       "df6fe73494a26f74da51573fd97b9baa"),
    ("tnt",        "ТНТ",          "546602986e6a424d74d594876ddb3f04"),
    ("ntv",        "НТВ",          "c37cd74192c6bc3d6cd6077c0c4fd686"),
    ("1tv",        "Первый канал", "c58f502c7bb34a8fcdd976b221fca292"),
    ("russia1",    "Россия 1",     "5cd8f08283e352a19829ecb269856b8b"),
    ("matchtv",    "Матч ТВ",      "11bbbec75a2ceb8cf446ad16813c6eec"),
    ("5tv",        "Пятый канал",  "b2b32a7d6f2323f3a113ff44b0404bf2"),
    ("kultura",    "Культура",     "5322070af872c4992d2d5237e2aa8809"),
    ("russia24",   "Россия 24",    "fd2c6d0222e5758dc781adc23b3f3491"),
    ("otr",        "ОТР",          "faa934385b83f9e8a92f5484defae5fa"),
    ("tvc",        "ТВЦ",          "92198c96552e3ee4a62cc1735a98ee54"),
    ("rentv",      "РЕН ТВ HD",    "54395b96ad1a7b49966f46a6eee370a4"),
    ("spas",       "СПАС",         "2bbfa9ebf9d79ade480d7281fcef1008"),
    ("sts",        "СТС HD",       "ffc110c6785e57f4c329179b555547b4"),
    ("dom",        "Домашний HD",  "49848b06c0fe2dae124419ffce1a1bab"),
    ("tv3",        "ТВ-3 HD",      "7bf12d9c050f9a7ef3728db5730432ae"),
    ("friday",     "Пятница HD",   "9f87a9a0cecbe773be6fddcbd93585ac"),
    ("tvzvezda",   "Звезда HD",    "5ab908fccfac5bb43ef2b1e4182256b0"),
    ("mir",        "Мир HD",       "afef67d151b5a607dee1ef0aa299a52c"),
    ("tnt4",       "ТНТ4",         "c801a7087e29a097192d74c270fbc6c1"),
    ("che",        "ЧЕ",           "6cde7d5b8a38bbaab829c71e45f95ba7"),
    ("u",          "Ю",            "5c9327074e25ca86f3111d4085cbbb65"),
    ("fonmusic",   "FON Music",    "5a294ae1ed12c44c7053301fb5fa9ba0"),
    ("mir24",      "Мир 24",       "43269ba8fb179e298b1e497f557e8d2d"),
    ("vballtv",    "Волейбол ТВ",  "cc1b56aa4955a144f324ad58998513bb"),
    ("solnce",     "Солнце",       "2dba20a8405e57935827cb5721c2b759"),
    ("soloviev",   "Соловьёв Live","c9b87c0b00cfff9b37f95b9c8e4eed42"),
    ("rbk",        "РБК Новости",  "88f6485ee28d56daf13302ac6fe3d931"),
    ("ctslove",    "СТС Love",     "32dc45cf878497abe1c9695e228f039b"),
    ("wasabi",     "Wasabi Anime", "ee3c34823d370bae91c0a7c1bd5b502c"),
    ("redbull",    "Red Bull TV",  "45b30eef1b89857182b03db2c25631d9"),
    ("kronehit",   "Kronehit TV",  "bc1b811349f526188c839d377913e16a"),
    ("soyuz",      "Союз",         "80b308e455f2aceb498e5dccd58ca050"),
    ("muzsoyuz",   "Муз Союз",     "d1dff14680d4c84e27908983375f7e89"),
    ("tsargrad",   "Царьград",     "91815da4edb167b5bd617bae490e57da"),
    ("360news",    "360 Новости",  "07beff61e617797db550cc3a5f6ad92b"),
    ("vmeste",     "ВМЕСТЕ РФ",    "f6a6d5c955180d0d0f80c66d0b6150d3"),
    ("ohotnik",    "Охотник и рыболов", "1da5d92af8c55b16241f1eb12a27f00c"),
   ("rutub tv",    "RUTUB TV", "9ae8e8a6dc58bdad66190475f9872ecd"),
   ("NHL",    "NHL EUROPE", "7a485ef5da9fe50ba939f36ca3e6ed96"),
   ("VIVA",    "VIVA RUSSIAN", "f712ae5ff3db23ec09b3674133d44daa"),
]

# STRICT junk/ad filtering
JUNK_DOMAINS = [
    "google-analytics", "googletagmanager", "doubleclick", "googleads",
    "yandex.ru", "yastatic.net", "mc.yandex", "ads.yandex",
    "facebook.com", "fbcdn.net", "twitter.com", "vk.com", "ok.ru",
    "adsystem", "adfox", "adriver", "betweendigital", "bidswitch",
    "adsrvr", "adform", "adnxs", "rubiconproject", "openx",
    "cdninstagram", "tiktok", "snapchat", "pinterest",
    "rutube.ru/api/", "rutube.ru/pic/", "rutube.ru/js/", "rutube.ru/css/",
    "/thumbnail/", "/poster/", "/preview/", "/cover/",
]

JUNK_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico",
                   ".js", ".css", ".html", ".xml", ".json", ".woff", ".woff2",
                   ".ttf", ".eot", ".mp3", ".mp4", ".webm", ".ogg"]

AD_PATTERNS = [
    r"ads?\.", r"advert", r"banner", r"preroll", r"midroll", r"postroll",
    r"commercial", r"sponsor", r"promo", r"tracking", r"metric", r"pixel",
    r"beacon", r"impression", r"clicktag", r"vast", r"vpaid", r"ima3",
]

VALID_STREAM_DOMAINS = [
    "bl.rutube.ru", "g2.rutube.ru", "balancer.rutube.ru",
    "stream.rutube.ru", "video.rutube.ru", "hls.rutube.ru",
    "dash.rutube.ru", "live.rutube.ru",
]

results = {}

def is_junk(url):
    u = url.lower()
    # Check junk domains
    for junk in JUNK_DOMAINS:
        if junk in u:
            return True
    # Check junk extensions
    for ext in JUNK_EXTENSIONS:
        if u.endswith(ext):
            return True
    # Check ad patterns
    for pattern in AD_PATTERNS:
        if re.search(pattern, u):
            return True
    return False

def is_stream(url):
    u = url.lower()
    # Must contain stream indicators
    has_stream_ext = any(x in u for x in (".m3u8", ".mpd", ".ts", ".m4s"))
    if not has_stream_ext:
        return False
    # Must be from valid domain or contain rutube
    has_valid_domain = any(d in u for d in VALID_STREAM_DOMAINS)
    has_rutube = "rutube" in u
    return has_valid_domain or has_rutube

def classify(url):
    u = url.lower()
    if ".mpd"  in u: return "dash"
    if ".m3u8" in u:
        if "/index.m3u8" in u or "/playlist.m3u8" in u:
            return "master"
        return "hls"
    if ".ts"   in u: return "ts"
    if ".m4s"  in u: return "m4s"
    return "unknown"

def normalize_url(url):
    return url.split("?")[0].split("#")[0].rstrip("/")

def url_belongs_to_channel(url, video_id):
    u = url.lower()
    vid = video_id.lower()
    # Direct video ID in URL
    if vid in u:
        return True
    # Valid rutube stream domain
    if any(d in u for d in VALID_STREAM_DOMAINS):
        return True
    # Contains livestream or video path with rutube
    if "rutube.ru" in u and ("/live/" in u or "/video/" in u or "/livestream/" in u):
        return True
    return False

# ========== METHOD 1: Network Interception ==========
async def method1_network(page, video_id):
    streams = []
    def on_response(resp):
        url = resp.url
        if resp.status >= 400 or is_junk(url) or not is_stream(url):
            return
        if not url_belongs_to_channel(url, video_id):
            return
        stype = classify(url)
        streams.append({"url": url, "type": stype, "method": "network"})
    page.on("response", on_response)
    return streams, on_response

# ========== METHOD 2: JS Extraction ==========
async def method2_js(page):
    js_streams = []
    try:
        config = await page.evaluate("""() => {
            var results = [];
            // Try RutubePlayer
            if (window.RutubePlayer && window.RutubePlayer.config) {
                results.push(JSON.stringify(window.RutubePlayer.config));
            }
            // Try initial state
            if (window.__INITIAL_STATE__ && window.__INITIAL_STATE__.video) {
                results.push(JSON.stringify(window.__INITIAL_STATE__.video));
            }
            // Try all window objects with video data
            for (var key in window) {
                try {
                    var val = window[key];
                    if (val && typeof val === 'object') {
                        var str = JSON.stringify(val);
                        if (str && (str.indexOf('.m3u8') !== -1 || str.indexOf('.mpd') !== -1)) {
                            results.push(str);
                        }
                    }
                } catch(e) {}
            }
            return results;
        }""")

        for cfg_str in config:
            try:
                data = json.loads(cfg_str)
                def extract_urls(obj):
                    urls = []
                    if isinstance(obj, dict):
                        for k, v in obj.items():
                            if isinstance(v, str) and is_stream(v) and not is_junk(v):
                                urls.append(v)
                            elif isinstance(v, (dict, list)):
                                urls.extend(extract_urls(v))
                    elif isinstance(obj, list):
                        for item in obj:
                            urls.extend(extract_urls(item))
                    return urls
                js_streams.extend(extract_urls(data))
            except:
                pass
    except Exception:
        pass
    return js_streams

# ========== METHOD 3: Direct API Call ==========
async def method3_api(page, video_id):
    api_streams = []
    try:
        # Rutube API endpoint for video info
        api_url = "https://rutube.ru/api/video/" + video_id + "/"
        response = await page.evaluate("""async (url) => {
            try {
                const res = await fetch(url, {headers: {'Accept': 'application/json'}});
                return await res.text();
            } catch(e) {
                return null;
            }
        }""", api_url)

        if response:
            data = json.loads(response)
            def extract_urls(obj):
                urls = []
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        if isinstance(v, str) and is_stream(v) and not is_junk(v):
                            urls.append(v)
                        elif isinstance(v, (dict, list)):
                            urls.extend(extract_urls(v))
                elif isinstance(obj, list):
                    for item in obj:
                        urls.extend(extract_urls(item))
                return urls
            api_streams = extract_urls(data)
    except Exception:
        pass
    return api_streams

async def scan_channel(page, ch_id, display_name, video_id):
    page_url = "https://rutube.ru/live/video/" + video_id + "/"
    all_streams = []

    # Method 1: Setup network interception
    net_streams, handler = await method1_network(page, video_id)

    try:
        # Load page
        await page.goto(page_url, timeout=NAV_TIMEOUT, wait_until="domcontentloaded")
        await page.wait_for_timeout(WAIT_MS)

        # Collect Method 1 results
        all_streams.extend(net_streams)

        # Method 2: JS extraction
        js_urls = await method2_js(page)
        for url in js_urls:
            if url_belongs_to_channel(url, video_id):
                all_streams.append({"url": url, "type": classify(url), "method": "js"})

        # Method 3: API call
        api_urls = await method3_api(page, video_id)
        for url in api_urls:
            if url_belongs_to_channel(url, video_id):
                all_streams.append({"url": url, "type": classify(url), "method": "api"})

    except Exception as ex:
        print("   X Oshibka: " + str(ex)[:60])
    finally:
        page.remove_listener("response", handler)

    # Deduplicate by normalized URL
    seen = {}
    unique = []
    for s in all_streams:
        key = normalize_url(s["url"])
        if key not in seen:
            seen[key] = True
            unique.append(s)

    results[ch_id] = {"display_name": display_name, "streams": unique}
    return len(unique)

async def run():
    global results
    results = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True,
            args=["--no-sandbox","--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            java_script_enabled=True)
        page = await context.new_page()

        print("\n" + "="*65)
        print("Skanirovanie " + str(len(CHANNELS)) + " kanalov")
        print("Metody: network + js + api | Strogaya filtratsiya reklamy")
        print("="*65 + "\n")

        for i, (ch_id, name, vid) in enumerate(CHANNELS, 1):
            print("[" + str(i).zfill(2) + "/" + str(len(CHANNELS)) + "] " + name.ljust(22) + " ", end="", flush=True)
            count = await scan_channel(page, ch_id, name, vid)
            print("-> " + str(count) + " potokov")

        await browser.close()

def save():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    m3u_path = os.path.join(OUTPUT_DIR, "rutube.m3u")
    count = 0

    with open(m3u_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write("#SOURCE:rutube.ru\n")
        f.write("#DATE:" + datetime.utcnow().isoformat() + "Z\n")
        f.write("#CHANNELS:" + str(len(CHANNELS)) + "\n")
        f.write("#METHOD:network+js+api\n")
        f.write("#FILTER:strict-ad-filter\n\n")

        for ch_id, display_name, _ in CHANNELS:
            data = results.get(ch_id, {})
            streams = data.get("streams", [])
            if not streams:
                continue

            display_safe = display_name.replace('"', "'")
            f.write('#EXTINF:-1 group-title="RuTube",' + display_safe + '\n')
            f.write("#EXTVLCOPT:http-referrer=https://rutube.ru/\n")

            for s in streams:
                stype = s["type"]
                if stype == "dash":
                    f.write("#KODIPROP:inputstreamaddon=inputstream.adaptive\n")
                    f.write("#KODIPROP:inputstream.adaptive.manifest_type=dash\n")
                f.write(s["url"] + "\n")

            f.write("\n")
            count += 1

    no_stream = [name for ch_id, name, _ in CHANNELS if not results.get(ch_id, {}).get("streams")]
    print("\n" + "="*65)
    print("Kanalov v M3U: " + str(count) + "/" + str(len(CHANNELS)))
    if no_stream:
        print("Bez potoka (" + str(len(no_stream)) + "): " + ", ".join(no_stream))
    print("Sohraneno: " + m3u_path)
    return count

async def main():
    t0 = time.time()
    print("RUTUBE SNIFFER -- TRIPLE METHOD v6")
    await run()
    count = save()
    print("\n" + str(int(time.time()-t0)) + " sek | " + str(count) + " kanalov")

if __name__ == "__main__":
    asyncio.run(main())
