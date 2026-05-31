#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RUTUBE LIVE SNIFFER — GITVERSE EDITION (FULLY FIXED)
- Исправлен listener cleanup
- Стабильная работа без вылетов
"""

import asyncio
import os
import json
import time
from datetime import datetime
from playwright.async_api import async_playwright

# ======================
# CONFIG
# ======================
ВЫХОДНАЯ_ПАПКА = "playlists/rutube"
ВРЕМЯ_ОЖИДАНИЯ = 15000  # Увеличил для надёжности
ТАЙМАУТ_НАВИГАЦИИ = 45000

# ======================
# CHANNELS (FULL 41)
# ======================
КАНАЛЫ = [
    ("plus_minus16", "1+/-16", "99d4597cea881a27cf7dd6e65a74dade"),
    ("2x2", "2x2", "392b4686b770bae2da6bf5ac4574add5"),
    ("rutv", "RU TV", "b1eb8e90d7e636677b3eb73b4fcbb717"),
    ("muztv", "MUZ TV", "df6fe73494a26f74da51573fd97b9baa"),
    ("tnt", "ТНТ", "546602986e6a424d74d594876ddb3f04"),
    ("ntv", "НТВ", "c37cd74192c6bc3d6cd6077c0c4fd686"),
    ("1tv", "Первый канал", "c58f502c7bb34a8fcdd976b221fca292"),
    ("russia1", "Россия 1", "5cd8f08283e352a19829ecb269856b8b"),
    ("matchtv", "Матч ТВ", "11bbbec75a2ceb8cf446ad16813c6eec"),
    ("5tv", "Пятый канал", "b2b32a7d6f2323f3a113ff44b0404bf2"),
    ("kultura", "Культура", "5322070af872c4992d2d5237e2aa8809"),
    ("russia24", "Россия 24", "fd2c6d0222e5758dc781adc23b3f3491"),
    ("otr", "ОТР", "faa934385b83f9e8a92f5484defae5fa"),
    ("tvc", "ТВЦ", "92198c96552e3ee4a62cc1735a98ee54"),
    ("rentv", "РЕН ТВ", "54395b96ad1a7b49966f46a6eee370a4"),
    ("spas", "СПАС", "2bbfa9ebf9d79ade480d7281fcef1008"),
    ("sts", "СТС", "ffc110c6785e57f4c329179b555547b4"),
    ("dom", "Домашний", "49848b06c0fe2dae124419ffce1a1bab"),
    ("tv3", "ТВ-3", "7bf12d9c050f9a7ef3728db5730432ae"),
    ("friday", "Пятница", "9f87a9a0cecbe773be6fddcbd93585ac"),
    ("zvezda", "Звезда", "5ab908fccfac5bb43ef2b1e4182256b0"),
    ("mir", "Мир", "afef67d151b5a607dee1ef0aa299a52c"),
    ("tnt4", "ТНТ4", "c801a7087e29a097192d74c270fbc6c1"),
    ("che", "ЧЕ", "6cde7d5b8a38bbaab829c71e45f95ba7"),
    ("yu", "Ю", "5c9327074e25ca86f3111d4085cbbb65"),
    ("solnce", "Солнце", "2dba20a8405e57935827cb5721c2b759"),
    ("rbk", "РБК", "88f6485ee28d56daf13302ac6fe3d931"),
    ("ctc_love", "СТС Love", "32dc45cf878497abe1c9695e228f039b"),
    ("fon_music", "Fon Music", "5a294ae1ed12c44c7053301fb5fa9ba0"),
    ("mir24", "Мир 24", "43269ba8fb179e298b1e497f557e8d2d"),
    ("volleyball_tv", "Волейбол ТВ", "cc1b56aa4955a144f324ad58998513bb"),
    ("soloviev_live", "Соловьёв Live", "c9b87c0b00cfff9b37f95b9c8e4eed42"),
    ("wasabi", "Wasabi Anime", "ee3c34823d370bae91c0a7c1bd5b502c"),
    ("redbull", "Red Bull TV", "45b30eef1b89857182b03db2c25631d9"),
    ("kronehit", "Kronehit TV", "bc1b811349f526188c839d377913e16a"),
    ("soyuz", "Союз", "80b308e455f2aceb498e5dccd58ca050"),
    ("muzsoyuz", "Муз Союз", "d1dff14680d4c84e27908983375f7e89"),
    ("tsargrad", "Царьград", "91815da4edb167b5bd617bae490e57da"),
    ("360", "360 Новости", "07beff61e617797db550cc3a5f6ad92b"),
    ("vmeste", "Вместе РФ", "f6a6d5c955180d0d0f80c66d0b6150d3"),
    ("ohota", "Охота и рыбалка", "1da5d92af8c55b16241f1eb12a27f00c"),
]

# ======================
# FILTERS
# ======================
МУСОР = ["google", "yandex", "doubleclick", "facebook", "vk.com", "analytics", "metric"]
EXT = [".jpg", ".png", ".css", ".js", ".html", ".woff", ".svg", ".ico"]

результаты = {}

def is_bad(url):
    u = url.lower()
    return any(x in u for x in МУСОР) or any(u.endswith(x) for x in EXT)

def is_stream(url):
    u = url.lower()
    return any(x in u for x in [".m3u8", ".mpd", ".ts", ".m4s"])

def norm(url):
    return url.split("?")[0].split("#")[0]

def type_stream(url):
    u = url.lower()
    if ".mpd" in u:
        return "dash"
    if ".m3u8" in u:
        return "hls"
    return "other"

# ======================
# JS EXTRACTION
# ======================
async def js(page):
    try:
        raw = await page.evaluate("""() => {
            let out = [];
            if (window.__INITIAL_STATE__) out.push(JSON.stringify(window.__INITIAL_STATE__));
            if (window.RutubePlayer) out.push(JSON.stringify(window.RutubePlayer));
            if (window.__RUTUBE_PLAYER_CONFIG__) out.push(JSON.stringify(window.__RUTUBE_PLAYER_CONFIG__));
            return out;
        }""")

        def walk(obj):
            res = []
            if isinstance(obj, dict):
                for v in obj.values():
                    if isinstance(v, str) and ("m3u8" in v or "mpd" in v):
                        res.append(v)
                    elif isinstance(v, (dict, list)):
                        res.extend(walk(v))
            elif isinstance(obj, list):
                for i in obj:
                    res.extend(walk(i))
            return res

        urls = []
        for s in raw:
            try:
                if s:
                    urls.extend(walk(json.loads(s)))
            except:
                pass

        return list(set(urls))
    except Exception as e:
        print(f"JS error: {e}")
        return []

# ======================
# API EXTRACTION
# ======================
async def api(page, vid):
    try:
        api_url = f"https://rutube.ru/api/video/{vid}/"

        text = await page.evaluate("""async (u) => {
            try {
                const r = await fetch(u, {
                    headers: { 'Accept': 'application/json' }
                });
                return await r.text();
            } catch(e) {
                return null;
            }
        }""", api_url)

        if not text:
            return []

        data = json.loads(text)

        def walk(obj):
            res = []
            if isinstance(obj, dict):
                for v in obj.values():
                    if isinstance(v, str) and ("m3u8" in v or "mpd" in v):
                        res.append(v)
                    elif isinstance(v, (dict, list)):
                        res.extend(walk(v))
            elif isinstance(obj, list):
                for i in obj:
                    res.extend(walk(i))
            return res

        return walk(data)
    except Exception as e:
        print(f"API error: {e}")
        return []

# ======================
# SCAN (FIXED — без утечек)
# ======================
async def scan(page, id_, name, vid):
    url = f"https://rutube.ru/live/video/{vid}/"
    
    # Собираем потоки
    streams = []
    seen_urls = set()
    
    # Обработчик ответов (без глобального listener)
    def on_response(response):
        try:
            resp_url = response.url
            if response.status >= 400:
                return
            if is_bad(resp_url):
                return
            if not is_stream(resp_url):
                return
            
            norm_url = norm(resp_url)
            if norm_url in seen_urls:
                return
            
            seen_urls.add(norm_url)
            streams.append({
                "url": resp_url,
                "type": type_stream(resp_url),
                "method": "network"
            })
        except:
            pass
    
    # Подписываемся
    page.on("response", on_response)
    
    try:
        # Переход на страницу
        try:
            await page.goto(url, timeout=ТАЙМАУТ_НАВИГАЦИИ, wait_until="domcontentloaded")
        except:
            await page.goto(f"https://rutube.ru/video/{vid}/", timeout=ТАЙМАУТ_НАВИГАЦИИ, wait_until="domcontentloaded")
        
        # Ждём загрузки
        await page.wait_for_timeout(ВРЕМЯ_ОЖИДАНИЯ)
        
        # JS метод
        js_urls = await js(page)
        for u in js_urls:
            norm_u = norm(u)
            if norm_u not in seen_urls:
                seen_urls.add(norm_u)
                streams.append({"url": u, "type": type_stream(u), "method": "js"})
        
        # API метод
        api_urls = await api(page, vid)
        for u in api_urls:
            norm_u = norm(u)
            if norm_u not in seen_urls:
                seen_urls.add(norm_u)
                streams.append({"url": u, "type": type_stream(u), "method": "api"})
    
    except Exception as e:
        print(f"Scan error for {name}: {e}")
    
    finally:
        # Отписываемся (ВАЖНО!)
        page.remove_listener("response", on_response)
    
    # Сохраняем результат
    результаты[id_] = {"name": name, "streams": streams}
    return len(streams)

# ======================
# RUN
# ======================
async def run():
    global результаты
    результаты = {}
    
    print("\n" + "="*60)
    print("RUTUBE LIVE SNIFFER — СТАБИЛЬНАЯ ВЕРСИЯ")
    print(f"Каналов: {len(КАНАЛЫ)}")
    print("="*60 + "\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        for i, (id_, name, vid) in enumerate(КАНАЛЫ, 1):
            print(f"[{i:02d}/{len(КАНАЛЫ)}] {name:30s}", end=" ", flush=True)
            count = await scan(page, id_, name, vid)
            print(f"-> {count} потоков")
        
        await browser.close()
    
    print("\n✅ Сканирование завершено")

# ======================
# SAVE
# ======================
def save():
    os.makedirs(ВЫХОДНАЯ_ПАПКА, exist_ok=True)
    
    m3u_path = os.path.join(ВЫХОДНАЯ_ПАПКА, "rutube.m3u")
    txt_path = os.path.join(ВЫХОДНАЯ_ПАПКА, "streams.txt")
    
    count = 0
    
    with open(m3u_path, "w", encoding="utf-8") as f_m3u:
        f_m3u.write("#EXTM3U\n")
        f_m3u.write(f"#SOURCE: RuTube\n")
        f_m3u.write(f"#DATE: {datetime.utcnow().isoformat()}Z\n")
        f_m3u.write(f"#CHANNELS: {len(КАНАЛЫ)}\n\n")
        
        with open(txt_path, "w", encoding="utf-8") as f_txt:
            for id_, name, _ in КАНАЛЫ:
                data = результаты.get(id_, {})
                streams = data.get("streams", [])
                
                if not streams:
                    continue
                
                f_m3u.write(f'#EXTINF:-1 group-title="RuTube",{name}\n')
                f_m3u.write("#EXTVLCOPT:http-referrer=https://rutube.ru/\n")
                
                for s in streams:
                    if s["type"] == "dash":
                        f_m3u.write("#KODIPROP:inputstreamaddon=inputstream.adaptive\n")
                        f_m3u.write("#KODIPROP:inputstream.adaptive.manifest_type=dash\n")
                    f_m3u.write(s["url"] + "\n")
                    f_txt.write(f"{name}|{s['url']}\n")
                
                f_m3u.write("\n")
                count += 1
    
    # Генерируем ссылку для GitVerse
    repo = os.environ.get("GITVERSE_REPOSITORY", os.environ.get("GITHUB_REPOSITORY", "user/repo"))
    branch = os.environ.get("GITVERSE_REF_NAME", os.environ.get("GITHUB_REF_NAME", "main"))
    
    raw_url = f"https://gitverse.ru/{repo}/raw/{branch}/{m3u_path.replace(os.sep, '/')}"
    
    # Сохраняем URL
    with open("RUTUBE_URL.txt", "w", encoding="utf-8") as f:
        f.write(raw_url)
    
    print("\n" + "="*60)
    print(f"📺 Сохранено: {m3u_path}")
    print(f"📊 Каналов с потоками: {count}/{len(КАНАЛЫ)}")
    print(f"🔗 RAW ссылка для плеера:")
    print(f"   {raw_url}")
    print("="*60)
    
    return count

# ======================
# MAIN
# ======================
async def main():
    start = time.time()
    
    try:
        await run()
        count = save()
        elapsed = time.time() - start
        print(f"\n⏱️ Время: {elapsed:.0f} сек | Каналов: {count}")
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)