#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IPTV ULTIMATE SNIFFER
Перехватывает HLS/DASH потоки с любых сайтов с видеоплеерами
"""

import asyncio
import os
import json
import re
import base64
import time
from datetime import datetime
from urllib.parse import urlparse, unquote, urljoin

from playwright.async_api import async_playwright

# ====== НАСТРОЙКИ ======
OUTPUT_DIR = "playlists"
WAIT_MS_PER_CHANNEL = 10000  # 10 секунд на канал
NAV_TIMEOUT = 45000  # 45 секунд на загрузку страницы
MAX_RETRIES = 2

# ====== ВСЕ ИСТОЧНИКИ ======
SITES = {
    "vitrina.tv": {
        "name": "Vitrina",
        "channels": [
            "che","1tvch","russia1","matchtv","ntv","5tv","kultura",
            "russia24","carusel","otr","tvc","rentv","spas","ctc",
            "dom","tv3","friday","tvzvezda","mir","tnt","muztv",
            "ctclove","u","solnce","subbota"
        ],
        "url_template": "https://vitrina.tv/#{channel}",
        "referrer": "https://vitrina.tv/",
        "player_selectors": [
            'video', 'video source', '[class*="player"]', '[id*="player"]',
            'iframe[src*="player"]', 'iframe[src*="video"]',
            '[class*="hls"]', '[class*="stream"]'
        ],
    },
    "smotret.tv": {
        "name": "SmotretTV",
        "channels": [
            "1-kanal","rossiya-1","tnt","ntv","subbota","tv-3",
            "pyatnica","yu","ctv","rbk","otr","tvc","zvezda",
            "ren-tv","sts","sts-love","domashniy","che",
            "5-kanal","kultura","mir","belros","360",
            "rossiya-24","moskva-doverie","karusel","spas",
            "muz-tv","2x2","perec","kvn","tnt4","zvezda-plus",
            "planeta-rtr","tvoe-tv","lentv24","sankt-peterburg"
        ],
        "url_template": "https://smotret.tv/{channel}",
        "referrer": "https://smotret.tv/",
        "player_selectors": [
            'video', '#player', '.player', 'iframe',
            '[class*="plyr"]', '[class*="video-js"]'
        ],
    },
    "televizor24tochka.ru": {
        "name": "Televizor24",
        "channels": [
            "pervyi-kanal","rossiya-1","rossiya-24","ntv","sts",
            "zvezda","muz-tv","karusel","match-tv","pyatnitsa",
            "5-kanal","tv-tsentr","otr","mir-tv","tnt","domashnii",
            "ren-tv","spas","tv-3","rossiya-kultura",
            "tavria","union","lugansk-24","zatv","krym-24",
            "pobeda","dom-kino","rt-d"
        ],
        "url_template": "https://televizor24tochka.ru/tv/{channel}.html",
        "referrer": "https://televizor24tochka.ru/",
        "player_selectors": [
            'video', '#player', 'iframe', '[src*="m3u8"]',
            '[class*="player"]', 'script'
        ],
    },
    "ontvtime.ru": {
        "name": "OnTVTime",
        "channels": [
            "1tv","russia1-tv","ntv-6","matchtv2","russiak-2",
            "tv3","russia24","tvc","rentv","tnt","sts3","zvezda",
            "channel5","karusel-2","otr","mir","mir24",
            "domashniy","moskva24","rbc","che","sts-love",
            "spas","iz","pyatnica","u","tnt4",
            "belarus1","belarus2","belarus3","belarus5",
            "belarus-ont","belarus-ctv","belarus-ntv",
            "belarus-rtr","belarus-perviy-informacionniy","belarus24"
        ],
        "url_template": "https://www.ontvtime.ru/live/{channel}.html",
        "referrer": "https://www.ontvtime.ru/",
        "player_selectors": [
            'video', 'iframe', '#player', '[class*="player"]'
        ],
    },
    "telik.live": {
        "name": "TelikLive",
        "channels": [
            "pervyj-kanal","rossiya-1","ntv","tnt","sts","tv-3",
            "pyatnitsa","match-tv","ren-tv","che","domashnij",
            "zvezda","pyatyj-kanal","karusel","otr","mir",
            "mir-24","moskva-24","rbk-tv","sts-love","tv-tsentr",
            "tnt4","kanal-yu","izvestiya","spas",
            "rossiya-kultura","rossiya-24","2x2","subbota","solntse"
        ],
        "url_template": "https://telik.live/{channel}.html",
        "referrer": "https://telik.live/",
        "player_selectors": [
            'video', 'iframe', '#player', '[class*="player"]',
            'script[src*="player"]'
        ],
    },
    "smotru.tv": {
        "name": "SmotruTV",
        "channels": [
            "pervyj-kanal","rossiya-1","ntv","ren","otr","tvc",
            "mir","zvezda","krasnaya-liniya","pyatyj-kanal",
            "rossiya-24","mir-24","rbk","moskva-24","karusel",
            "tnt","sts","tnt4","2x2","kanal-che","pyatnitsa-tv",
            "kanal-you","muz-tv","tnt-music","dom-kino","tv-3",
            "disney","rtg","rtg-hd"
        ],
        "url_template": "https://smotru.tv/{channel}.html",
        "referrer": "https://smotru.tv/",
        "player_selectors": [
            'video', 'iframe', '[class*="player"]', 'script'
        ],
    },
    "spbtvonline.ru": {
        "name": "SPBTVOnline",
        "channels": [
            "pervyi-kanal","rossiia1","rossiya_24","ntv",
            "rossiya-kultura","sts","zvezda","muz-tv","karusel",
            "match-tv","tnt","ren-tv","5-kanal","tv-tsentr",
            "otr","mir-tv","domashnii","tv-3","spas","u",
            "tnt4","subbota","che","yu","lentv24",
            "sankt-peterburg","moskva-24","rbk","360"
        ],
        "url_template": "https://spbtvonline.ru/kanaly-tv/{channel}.html",
        "referrer": "https://spbtvonline.ru/",
        "player_selectors": [
            'video', 'iframe', '[class*="player"]', '#player'
        ],
    },
    "rutuner.ru": {
        "name": "Rutuner",
        "channels": [
            "pervyy-kanal","rossiya-1","ntv","ren-tv","pyatnica",
            "tnt","sts","zvezda","pyatyy-kanal","tv-centr",
            "otr","mir","domashniy","che","yu","tnt-4",
            "match-tv","rossiya-24","rbk","muz-tv",
            "karusel","spas","tv-3","kanal-disney","subbota",
            "sts-love","tnt-music","moskva-24"
        ],
        "url_template": "http://rutuner.ru/watch/{channel}",
        "referrer": "http://rutuner.ru/",
        "player_selectors": [
            'video', 'iframe', '#player', '[class*="player"]'
        ],
    },
}

# ====== ХРАНИЛИЩЕ ======
results = {}

def ensure_entry(site, ch):
    key = f"{site}:{ch}"
    if key not in results:
        results[key] = {
            "site": site,
            "channel": ch,
            "hls": set(),
            "dash": set(),
            "stream_urls": set(),  # любые потоки
            "drm": False,
            "seen_hosts": set(),
            "last_seen": None,
            "player_found": False,
            "error": None,
        }
    return results[key]

def host(url: str):
    try:
        return urlparse(url).netloc
    except:
        return ""

def extract_urls_from_text(text: str) -> list:
    """Extract all URLs including base64 encoded ones"""
    urls = []
    
    # Direct m3u8/mpd URLs
    for pattern in [
        r'(https?://[^\s<>"\'{}|\\^`\[\]]+\.m3u8[^\s<>"\'{}|\\^`\[\]]*)',
        r'(https?://[^\s<>"\'{}|\\^`\[\]]+\.mpd[^\s<>"\'{}|\\^`\[\]]*)',
        r'(https?://[^\s<>"\'{}|\\^`\[\]]+\.ts[^\s<>"\'{}|\\^`\[\]]*)',
        r'(https?://[^\s<>"\'{}|\\^`\[\]]+/hls[^\s<>"\'{}|\\^`\[\]]*)',
        r'(https?://[^\s<>"\'{}|\\^`\[\]]+/dash[^\s<>"\'{}|\\^`\[\]]*)',
        r'(https?://[^\s<>"\'{}|\\^`\[\]]*m3u8[^\s<>"\'{}|\\^`\[\]]*)',
        r'(https?://[^\s<>"\'{}|\\^`\[\]]*manifest[^\s<>"\'{}|\\^`\[\]]*)',
        r'(https?://[^\s<>"\'{}|\\^`\[\]]*playlist[^\s<>"\'{}|\\^`\[\]]*)',
        r'(//[^\s<>"\'{}|\\^`\[\]]+\.m3u8[^\s<>"\'{}|\\^`\[\]]*)',
        r'(//[^\s<>"\'{}|\\^`\[\]]+\.mpd[^\s<>"\'{}|\\^`\[\]]*)',
    ]:
        matches = re.findall(pattern, text, re.IGNORECASE)
        urls.extend(matches)
    
    # Try to decode base64 strings
    b64_patterns = [
        r'["\']([A-Za-z0-9+/=]{50,})["\']',
        r'atob\(["\']([^"\']+)["\']\)',
    ]
    for pattern in b64_patterns:
        for match in re.findall(pattern, text):
            try:
                decoded = base64.b64decode(match).decode('utf-8', errors='ignore')
                if 'http' in decoded or 'm3u8' in decoded or 'mpd' in decoded:
                    urls.extend(extract_urls_from_text(decoded))
            except:
                pass
    
    # URL-encoded URLs
    encoded_pattern = r'(https?%3A%2F%2F[^\s<>"\'{}|\\^`\[\]]+)'
    for match in re.findall(encoded_pattern, text):
        try:
            decoded = unquote(match)
            if '.m3u8' in decoded or '.mpd' in decoded or '/hls' in decoded:
                urls.append(decoded)
        except:
            pass
    
    return list(set(urls))

def is_stream_url(url: str) -> bool:
    """Check if URL is a valid stream"""
    low = url.lower()
    
    # Skip analytics and ads
    skip_domains = (
        "stat-analytics", "mc.yandex", "counter.yadro",
        "tns-counter", "google-analytics", "dmg.digitaltarget",
        "yandex.ru/metrika", "yastatic.net", "bs.serving-sys",
        "googletagmanager", "doubleclick", "facebook.com/tr"
    )
    if any(d in low for d in skip_domains):
        return False
    
    # Stream indicators
    stream_indicators = (
        '.m3u8', '.mpd', '.ts', '.m4s', '.cmfv', '.cmfa',
        '/hls-', '/dash-', '/hls/', '/dash/',
        'hls-live', 'dash-live', 'hls_live', 'dash_live',
        'manifest', 'playlist.m3u', 'chunklist',
        'token=v2.', 'edge0', 'edge-', 'cdn.',
        'livef', 'livetv', 'stream', 'broadcast'
    )
    
    if any(i in low for i in stream_indicators):
        return True
    
    return False

def extract_from_js(code: str) -> list:
    """Extract stream URLs from JavaScript code"""
    urls = []
    
    # Common JS patterns for video players
    patterns = [
        r'["\'](https?://[^"\']*?\.m3u8[^"\']*)["\']',
        r'["\'](https?://[^"\']*?\.mpd[^"\']*)["\']',
        r'["\'](https?://[^"\']*?/hls[^"\']*)["\']',
        r'["\'](https?://[^"\']*?/dash[^"\']*)["\']',
        r'src\s*:\s*["\']([^"\']*?m3u8[^"\']*)["\']',
        r'src\s*:\s*["\']([^"\']*?mpd[^"\']*)["\']',
        r'file\s*:\s*["\']([^"\']*?)["\']',
        r'source\s*:\s*["\']([^"\']*?)["\']',
        r'url\s*:\s*["\']([^"\']*?)["\']',
        r'stream\s*:\s*["\']([^"\']*?)["\']',
        r'videoUrl\s*:\s*["\']([^"\']*?)["\']',
        r'video_url\s*:\s*["\']([^"\']*?)["\']',
        r'playlistUrl\s*:\s*["\']([^"\']*?)["\']',
        r'hlsUrl\s*:\s*["\']([^"\']*?)["\']',
        r'dashUrl\s*:\s*["\']([^"\']*?)["\']',
        # JW Player
        r'file\s*:\s*["\']([^"\']*?)["\']',
        # VideoJS
        r'sources\s*:\s*\[\s*\{\s*src\s*:\s*["\']([^"\']*?)["\']',
        # Flowplayer
        r'clip\s*:\s*\{\s*url\s*:\s*["\']([^"\']*?)["\']',
        # Common player configs
        r'["\']hls["\']\s*:\s*["\']([^"\']*?)["\']',
        r'["\']dash["\']\s*:\s*["\']([^"\']*?)["\']',
        r'["\']streamUrl["\']\s*:\s*["\']([^"\']*?)["\']',
        r'player\.setup\([^)]*file\s*:\s*["\']([^"\']*?)["\']',
    ]
    
    for pattern in patterns:
        for match in re.findall(pattern, code, re.IGNORECASE):
            if match and len(match) > 10:
                urls.append(match)
    
    # JSON embedded in JS
    json_blocks = re.findall(r'(\{[^{}]*?(?:m3u8|mpd|hls|dash|stream|playlist)[^{}]*?\})', code, re.IGNORECASE)
    for block in json_blocks:
        try:
            data = json.loads(block)
            for key in ('src', 'file', 'url', 'source', 'stream', 'hls', 'dash', 'video', 'playlist'):
                if key in data:
                    val = data[key]
                    if isinstance(val, str) and len(val) > 10:
                        urls.append(val)
                    elif isinstance(val, list):
                        for item in val:
                            if isinstance(item, dict):
                                for k in ('src', 'file', 'url'):
                                    if k in item:
                                        urls.append(item[k])
                            elif isinstance(item, str) and len(item) > 10:
                                urls.append(item)
        except:
            pass
    
    return [u for u in urls if u.startswith('http') or u.startswith('//')]

async def sniff_page(page, url: str, site_key: str, channel: str, referrer: str):
    """
    Aggressive sniffing of a single page
    """
    entry = ensure_entry(site_key, channel)
    all_streams = set()
    
    # Set referrer
    await page.set_extra_http_headers({"Referer": referrer})
    
    for attempt in range(MAX_RETRIES + 1):
        try:
            # Load page
            resp = await page.goto(url, timeout=NAV_TIMEOUT, wait_until="networkidle")
            
            # Get all response bodies from the page load
            if resp:
                body = await resp.text()
                
                # Check if the HTML itself contains stream URLs
                html_urls = extract_urls_from_text(body)
                for u in html_urls:
                    if is_stream_url(u):
                        all_streams.add(u)
                
                # Check JavaScript in HTML
                script_urls = extract_from_js(body)
                for u in script_urls:
                    if is_stream_url(u):
                        all_streams.add(u)
            
            # Wait for dynamic loading
            await page.wait_for_timeout(WAIT_MS_PER_CHANNEL)
            
            # Get complete page content after JS execution
            full_html = await page.content()
            html_urls = extract_urls_from_text(full_html)
            for u in html_urls:
                if is_stream_url(u):
                    all_streams.add(u)
            
            # Execute JS to find video elements
            video_info = await page.evaluate("""() => {
                const results = [];
                
                // Check video elements
                const videos = document.querySelectorAll('video');
                for (const v of videos) {
                    if (v.src) results.push(v.src);
                    if (v.currentSrc) results.push(v.currentSrc);
                    
                    // Check source elements
                    const sources = v.querySelectorAll('source');
                    for (const s of sources) {
                        if (s.src) results.push(s.src);
                    }
                }
                
                // Check common player variables
                const playerChecks = [
                    'player', 'jwplayer', 'flowplayer', 'videojs',
                    'hls', 'dash', 'stream', 'playlist',
                    'playerInstance', 'videoPlayer', 'streamUrl',
                    'hlsUrl', 'dashUrl', 'playlistUrl'
                ];
                
                for (const key of playerChecks) {
                    try {
                        const obj = window[key];
                        if (!obj) continue;
                        
                        // Get all string properties
                        const str = JSON.stringify(obj, (k, v) => {
                            if (typeof v === 'string' && v.length < 2000) return v;
                            if (typeof v === 'function') return undefined;
                            return v;
                        });
                        
                        if (str) results.push(str);
                    } catch(e) {}
                }
                
                // Check all script tags
                const scripts = document.querySelectorAll('script');
                for (const s of scripts) {
                    if (s.textContent) results.push(s.textContent);
                    if (s.src) results.push(s.src);
                }
                
                // Check localStorage and sessionStorage
                try {
                    for (let i = 0; i < localStorage.length; i++) {
                        const key = localStorage.key(i);
                        const val = localStorage.getItem(key);
                        if (val && val.length < 5000) results.push(val);
                    }
                    for (let i = 0; i < sessionStorage.length; i++) {
                        const key = sessionStorage.key(i);
                        const val = sessionStorage.getItem(key);
                        if (val && val.length < 5000) results.push(val);
                    }
                } catch(e) {}
                
                return results;
            }""")
            
            # Extract URLs from all JS data
            for item in video_info:
                if isinstance(item, str):
                    js_urls = extract_from_js(item)
                    for u in js_urls:
                        if is_stream_url(u):
                            all_streams.add(u)
                    text_urls = extract_urls_from_text(item)
                    for u in text_urls:
                        if is_stream_url(u):
                            all_streams.add(u)
            
            # Process iframes
            iframes = await page.query_selector_all('iframe')
            for iframe in iframes:
                try:
                    src = await iframe.get_attribute('src')
                    if src:
                        if is_stream_url(src):
                            all_streams.add(src)
                        
                        # Try to access iframe content
                        try:
                            frame = await iframe.content_frame()
                            if frame:
                                frame_html = await frame.content()
                                frame_urls = extract_urls_from_text(frame_html)
                                for u in frame_urls:
                                    if is_stream_url(u):
                                        all_streams.add(u)
                                
                                # Execute JS in iframe
                                frame_data = await frame.evaluate("""() => {
                                    const results = [];
                                    const videos = document.querySelectorAll('video');
                                    for (const v of videos) {
                                        if (v.src) results.push(v.src);
                                        if (v.currentSrc) results.push(v.currentSrc);
                                    }
                                    const scripts = document.querySelectorAll('script');
                                    for (const s of scripts) {
                                        if (s.textContent) results.push(s.textContent);
                                    }
                                    return results;
                                }""")
                                
                                for item in frame_data:
                                    if isinstance(item, str):
                                        frame_urls2 = extract_urls_from_text(item)
                                        for u in frame_urls2:
                                            if is_stream_url(u):
                                                all_streams.add(u)
                        except:
                            pass
                except:
                    pass
            
            if all_streams:
                break
                
        except Exception as e:
            if attempt < MAX_RETRIES:
                await page.wait_for_timeout(3000)
                continue
            entry["error"] = str(e)[:200]
    
    # Process found streams
    for url in all_streams:
        url = url.strip().strip('"').strip("'")
        if url.startswith('//'):
            url = 'https:' + url
        
        entry["stream_urls"].add(url)
        entry["seen_hosts"].add(host(url))
        
        low = url.lower()
        if any(x in low for x in ("widevine", "license", "drm", "clearkey")):
            entry["drm"] = True
        
        if '.m3u8' in low or '/hls' in low:
            entry["hls"].add(url)
            print(f"      [HLS] {url[:100]}")
        elif '.mpd' in low or '/dash' in low:
            entry["dash"].add(url)
            print(f"      [DASH] {url[:100]}")
        elif is_stream_url(low):
            entry["hls"].add(url)
            print(f"      [STREAM] {url[:100]}")
    
    entry["last_seen"] = datetime.utcnow().isoformat()
    
    if all_streams:
        entry["player_found"] = True
        print(f"      ✅ Найдено потоков: {len(all_streams)}")
    else:
        print(f"      ❌ Потоки не найдены")
    
    return all_streams

async def validate_stream(context, url: str, timeout=10000) -> bool:
    """Validate HLS/DASH stream"""
    try:
        resp = await context.request.get(url, timeout=timeout, 
                                          headers={"Referer": "https://vitrina.tv/"})
        if resp.ok:
            text = await resp.text()
            # Check for valid M3U8
            if '.m3u8' in url.lower():
                return '#EXTM3U' in text[:500] or '#EXTINF' in text[:500]
            # Check for valid MPD
            if '.mpd' in url.lower():
                return '<MPD' in text[:500] or 'xmlns' in text[:500]
            # Generic check
            return len(text) > 100
    except:
        pass
    return False

async def process_site(browser, site_key, site_config):
    """Process all channels for one site"""
    name = site_config["name"]
    channels = site_config["channels"]
    template = site_config["url_template"]
    referrer = site_config.get("referrer", "")
    
    print(f"\n{'='*70}")
    print(f"📡 {name} ({len(channels)} каналов)")
    print(f"{'='*70}")
    
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        java_script_enabled=True,
        viewport={"width": 1920, "height": 1080},
        ignore_https_errors=True,
    )
    
    page = await context.new_page()
    
    # Intercept ALL responses
    def make_response_handler(site=site_key):
        def handler(resp):
            url = resp.url
            low = url.lower()
            
            # Skip non-stream responses
            if resp.status >= 400:
                return
            if any(x in low for x in ('.jpg', '.png', '.gif', '.css', '.woff', '.ico', '.svg')):
                return
            
            # Check for stream URLs in ALL responses
            if is_stream_url(low):
                for ch in channels:
                    # Try to match channel with URL or response body
                    if ch.replace('-', '') in low.replace('-', '') or ch in low:
                        entry = ensure_entry(site, ch)
                        if '.m3u8' in low:
                            entry["hls"].add(url)
                        elif '.mpd' in low:
                            entry["dash"].add(url)
                        entry["stream_urls"].add(url)
                        entry["seen_hosts"].add(host(url))
                        entry["last_seen"] = datetime.utcnow().isoformat()
                        print(f"      [RESP] {ch} -> {url[:100]}")
                        break
        return handler
    
    page.on("response", make_response_handler())
    
    for i, ch in enumerate(channels):
        url = template.format(channel=ch)
        print(f"\n  [{i+1}/{len(channels)}] {ch}")
        print(f"      URL: {url}")
        
        await sniff_page(page, url, site_key, ch, referrer)
        
        # Small delay between channels
        await page.wait_for_timeout(2000)
    
    await context.close()

async def validate_all_streams():
    """Validate all found streams"""
    print(f"\n{'='*70}")
    print("🔍 ВАЛИДАЦИЯ ПОТОКОВ")
    print(f"{'='*70}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context()
        
        total_validated = 0
        total_valid = 0
        
        for key, entry in results.items():
            if not entry["hls"]:
                continue
            
            site_name = SITES.get(entry["site"], {}).get("name", entry["site"])
            channel = entry["channel"]
            
            valid_urls = set()
            for url in list(entry["hls"])[:10]:
                total_validated += 1
                is_valid = await validate_stream(context, url)
                if is_valid:
                    valid_urls.add(url)
                    total_valid += 1
                    print(f"  ✅ {site_name}/{channel}: {url[:80]}")
                else:
                    print(f"  ❌ {site_name}/{channel}: невалидный")
            
            entry["hls"] = valid_urls
        
        await browser.close()
        
        print(f"\n  Всего проверено: {total_validated}")
        print(f"  Валидных: {total_valid}")
        print(f"  Невалидных: {total_validated - total_valid}")

def save_all():
    """Save all results"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Group by site
    by_site = {}
    for key, entry in results.items():
        site = entry["site"]
        if site not in by_site:
            by_site[site] = {}
        by_site[site][entry["channel"]] = {
            "hls": sorted(list(entry["hls"])),
            "dash": sorted(list(entry["dash"])),
            "stream_urls": sorted(list(entry["stream_urls"])),
            "drm": bool(entry["drm"]),
            "hosts": sorted(list(entry["seen_hosts"])),
            "last_seen": entry["last_seen"],
            "player_found": entry["player_found"],
        }
    
    # Save per-site JSON and M3U
    for site_name, channels in by_site.items():
        site_dir = os.path.join(OUTPUT_DIR, site_name)
        os.makedirs(site_dir, exist_ok=True)
        
        # JSON
        json_path = os.path.join(site_dir, "streams.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(channels, f, indent=2, ensure_ascii=False)
        
        # M3U
        site_config = SITES.get(site_name, {})
        site_title = site_config.get("name", site_name)
        referrer = site_config.get("referrer", "")
        
        m3u_path = os.path.join(site_dir, f"{site_name}.m3u")
        with open(m3u_path, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            f.write(f"#SITE:{site_title}\n")
            f.write(f"#DATE:{datetime.utcnow().isoformat()}Z\n\n")
            
            for ch_name, ch_data in sorted(channels.items()):
                for u in ch_data["hls"]:
                    f.write(f'#EXTINF:-1 group-title="{site_title}",{ch_name}\n')
                    if referrer:
                        f.write(f"#EXTVLCOPT:http-referrer={referrer}\n")
                    f.write(f"#EXTVLCOPT:http-user-agent=Mozilla/5.0\n")
                    f.write(f"{u}\n\n")
        
        print(f"  [OK] {site_title}: {len(channels)} каналов -> {os.path.basename(m3u_path)}")
    
    # Combined M3U
    all_m3u = os.path.join(OUTPUT_DIR, "ALL_STREAMS.m3u")
    total = 0
    with open(all_m3u, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write(f"#DATE:{datetime.utcnow().isoformat()}Z\n")
        f.write(f"#TOTAL_SITES:{len(by_site)}\n\n")
        
        for site_name, channels in sorted(by_site.items()):
            site_config = SITES.get(site_name, {})
            site_title = site_config.get("name", site_name)
            referrer = site_config.get("referrer", "")
            
            for ch_name, ch_data in sorted(channels.items()):
                for u in ch_data["hls"]:
                    f.write(f'#EXTINF:-1 group-title="{site_title}",{ch_name}\n')
                    if referrer:
                        f.write(f"#EXTVLCOPT:http-referrer={referrer}\n")
                    f.write(f"#EXTVLCOPT:http-user-agent=Mozilla/5.0\n")
                    f.write(f"{u}\n\n")
                    total += 1
    
    print(f"\n  [OK] ОБЩИЙ M3U: {all_m3u}")
    print(f"  [OK] Всего каналов: {total}")
    
    # Combined JSON
    combined_json = os.path.join(OUTPUT_DIR, "all_sites.json")
    with open(combined_json, "w", encoding="utf-8") as f:
        json.dump(by_site, f, indent=2, ensure_ascii=False)
    
    return total

async def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║         🚀 IPTV ULTIMATE SNIFFER v2.0                        ║
║         Агрессивный сбор HLS/DASH со всех сайтов            ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    t0 = time.time()
    
    # Launch browser
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--ignore-certificate-errors",
            ]
        )
        
        total_sites = len(SITES)
        for i, (site_key, site_config) in enumerate(SITES.items(), 1):
            print(f"\n{'#'*70}")
            print(f"# САЙТ {i}/{total_sites}: {site_config['name']}")
            print(f"{'#'*70}")
            
            try:
                await process_site(browser, site_key, site_config)
            except Exception as e:
                print(f"  ❌ Ошибка сайта: {str(e)[:200]}")
        
        await browser.close()
    
    # Validate streams
    await validate_all_streams()
    
    # Save results
    total_channels = save_all()
    
    dt = time.time() - t0
    
    print(f"\n{'='*70}")
    print(f"🎉 ГОТОВО!")
    print(f"{'='*70}")
    print(f"  📊 Статистика:")
    print(f"     Сайтов обработано: {len(SITES)}")
    print(f"     Всего каналов в M3U: {total_channels}")
    print(f"     Время: {dt:.1f} сек")
    print(f"  📁 Результаты: {os.path.abspath(OUTPUT_DIR)}/")
    print(f"  📥 Главный плейлист: {os.path.abspath(OUTPUT_DIR)}/ALL_STREAMS.m3u")

if __name__ == "__main__":
    asyncio.run(main())