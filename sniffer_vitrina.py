#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VITRINA.TV SNIFFER — FULL FIX
- Сохраняет ВСЕ найденные потоки
- Лучший поток выбирается, но ВСЕ пишутся в M3U
- Исправлена статистика
- Стабильная работа
"""

import asyncio
import os
import time
from datetime import datetime
from playwright.async_api import async_playwright

# ====== НАСТРОЙКИ ======
ВЫХОДНАЯ_ПАПКА = "playlists/vitrina"
ВРЕМЯ_ОЖИДАНИЯ = 8000  # Увеличил до 8 секунд
ВРЕМЯ_ПОВТОРА = 5000
ТАЙМАУТ_НАВИГАЦИИ = 20000

# ====== КАНАЛЫ ======
КАНАЛЫ = [
    ("che", "https://vitrina.tv/#che", "ЧЕ"),
    ("1tvch", "https://vitrina.tv/#1tvch", "Первый канал"),
    ("russia1", "https://vitrina.tv/#russia1", "Россия 1"),
    ("matchtv", "https://vitrina.tv/#matchtv", "Матч ТВ"),
    ("ntv", "https://vitrina.tv/#ntv", "НТВ"),
    ("5tv", "https://vitrina.tv/#5tv", "Пятый канал"),
    ("kultura", "https://vitrina.tv/#kultura", "Культура"),
    ("russia24", "https://vitrina.tv/#russia24", "Россия 24"),
    ("carusel", "https://vitrina.tv/#carusel", "Карусель"),
    ("otr", "https://vitrina.tv/#otr", "ОТР"),
    ("tvc", "https://vitrina.tv/#tvc", "ТВЦ"),
    ("rentv", "https://vitrina.tv/#rentv", "РЕН ТВ"),
    ("spas", "https://vitrina.tv/#spas", "СПАС"),
    ("ctc", "https://vitrina.tv/#ctc", "СТС"),
    ("dom", "https://vitrina.tv/#dom", "Домашний"),
    ("tv3", "https://vitrina.tv/#tv3", "ТВ-3"),
    ("friday", "https://vitrina.tv/#friday", "Пятница"),
    ("tvzvezda", "https://vitrina.tv/#tvzvezda", "Звезда"),
    ("mir", "https://vitrina.tv/#mir", "МИР"),
    ("tnt", "https://vitrina.tv/#tnt", "ТНТ"),
    ("muztv", "https://vitrina.tv/#muztv", "МУЗ-ТВ"),
    ("ctclove", "https://vitrina.tv/#ctclove", "СТС Love"),
    ("u", "https://vitrina.tv/#u", "Ю"),
    ("solnce", "https://vitrina.tv/#solnce", "Солнце"),
    ("subbota", "https://vitrina.tv/#subbota", "Суббота"),
]

# ====== ФИЛЬТРЫ ======
МУСОРНЫЕ_ДОМЕНЫ = [
    "mc.yandex.ru", "yastatic.net", "google-analytics.com",
    "googletagmanager.com", "doubleclick.net", "tns-counter.ru",
    "stbid.ru", "telecid.ru", "stat-analytics.com",
    "counter.yadro.ru", "bs.serving-sys.com",
]

результаты = {}
текущий_канал = None
блокировка_канала = asyncio.Lock()


def это_поток(url: str) -> bool:
    """Проверяет, является ли URL потоком"""
    u = url.lower()
    
    # Пропускаем HTML
    if u.endswith(".html") or u.endswith(".htm") or "/player.html" in u:
        return False
    
    # Расширения потоков
    if any(ext in u for ext in [".m3u8", ".mpd", ".ts", ".m4s", ".cmfv", ".cmfa"]):
        return True
    
    # Ключевые слова потока
    ключевые_слова = [
        "hls-live", "dash-live", "tracks-v", "index.m3u8", 
        "manifest.mpd", "live/", "/hls/", "/dash/", "mediavitrina", 
        "cdnvideo", "edgecdn", "livestream", "playlist.m3u8",
        "chunklist", "master.m3u8"
    ]
    
    return any(k in u for k in ключевые_слова)


def это_мусор(url: str) -> bool:
    """Проверяет, является ли URL мусором"""
    u = url.lower()
    return any(d in u for d in МУСОРНЫЕ_ДОМЕНЫ)


def определить_тип(url: str) -> str:
    """Определяет тип потока"""
    u = url.lower()
    if ".mpd" in u:
        return "dash"
    if ".m3u8" in u:
        if "master.m3u8" in u or "index.m3u8" in u:
            return "master"
        return "hls"
    if ".ts" in u:
        return "ts"
    if ".m4s" in u:
        return "m4s"
    return "other"


def выбрать_лучший_поток(потоки):
    """Выбирает лучший поток по приоритету"""
    приоритет = {"master": 0, "hls": 1, "dash": 2, "ts": 3, "m4s": 4, "other": 5}
    if not потоки:
        return None
    return sorted(потоки, key=lambda s: приоритет.get(s["type"], 99))[0]


async def сканировать_канал(контекст, ид, url, название, delay, проход, номер, всего):
    """Сканирует один канал"""
    global текущий_канал
    
    if ид not in результаты:
        результаты[ид] = {"name": название, "streams": []}
    
    print(f"[{проход}] [{номер}/{всего}] {название:25s}", end=" ", flush=True)
    
    собранные = []
    seen_urls = set()
    
    async def обработчик_ответа(ответ):
        async with блокировка_канала:
            if текущий_канал != ид:
                return
        
        url_ответа = ответ.url
        
        if ответ.status >= 400:
            return
        if это_мусор(url_ответа):
            return
        if not это_поток(url_ответа):
            return
        
        # Нормализуем URL для дедупликации
        norm_url = url_ответа.split('?')[0].split('#')[0]
        if norm_url in seen_urls:
            return
        
        seen_urls.add(norm_url)
        собранные.append({
            "url": url_ответа, 
            "type": определить_тип(url_ответа)
        })
    
    страница = await контекст.new_page()
    контекст.on("response", обработчик_ответа)
    
    async with блокировка_канала:
        текущий_канал = ид
    
    try:
        await страница.goto(url, timeout=ТАЙМАУТ_НАВИГАЦИИ, wait_until="domcontentloaded")
        await страница.wait_for_timeout(delay)
    except Exception as e:
        print(f"✗ Ошибка: {str(e)[:50]}")
    finally:
        async with блокировка_канала:
            текущий_канал = None
        await страница.close()
    
    # Добавляем новые потоки
    новых = 0
    for s in собранные:
        if not any(x["url"] == s["url"] for x in результаты[ид]["streams"]):
            результаты[ид]["streams"].append(s)
            новых += 1
    
    всего_потоков = len(результаты[ид]["streams"])
    print(f"✓ (найдено: {len(собранные)}, всего: {всего_потоков})")


async def запустить():
    """Запускает сканирование всех каналов"""
    global результаты, текущий_канал
    
    результаты = {}
    текущий_канал = None
    
    async with async_playwright() as p:
        браузер = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        контекст = await браузер.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        
        print("\n" + "=" * 70)
        print(f"🔍 VITRINA TV СНИФФЕР")
        print(f"📡 Каналов: {len(КАНАЛЫ)}")
        print(f"⏱️  Ожидание: {ВРЕМЯ_ОЖИДАНИЯ/1000} сек на канал")
        print("=" * 70 + "\n")
        
        # Первый проход
        for i, (id_, url, name) in enumerate(КАНАЛЫ, 1):
            await сканировать_канал(
                контекст, id_, url, name,
                ВРЕМЯ_ОЖИДАНИЯ, "1", i, len(КАНАЛЫ)
            )
        
        # Второй проход для каналов без потоков
        failed = [(id_, url, name) for id_, url, name in КАНАЛЫ 
                  if not результаты.get(id_, {}).get("streams")]
        
        if failed:
            print(f"\n{'=' * 70}")
            print(f"🔄 ВТОРОЙ ПРОХОД — {len(failed)} каналов без потоков")
            print("=" * 70 + "\n")
            
            for i, (id_, url, name) in enumerate(failed, 1):
                await сканировать_канал(
                    контекст, id_, url, name,
                    ВРЕМЯ_ПОВТОРА, "2", i, len(failed)
                )
        
        await браузер.close()


def сохранить():
    """Сохраняет результаты в M3U"""
    os.makedirs(ВЫХОДНАЯ_ПАПКА, exist_ok=True)
    
    m3u_path = os.path.join(ВЫХОДНАЯ_ПАПКА, "vitrina.m3u")
    txt_path = os.path.join(ВЫХОДНАЯ_ПАПКА, "stream_urls.txt")
    
    channels_with_streams = 0
    total_streams = 0
    
    with open(m3u_path, "w", encoding="utf-8") as f_m3u, \
         open(txt_path, "w", encoding="utf-8") as f_txt:
        
        f_m3u.write("#EXTM3U\n")
        f_m3u.write(f"#SOURCE: vitrina.tv\n")
        f_m3u.write(f"#DATE: {datetime.utcnow().isoformat()}Z\n")
        f_m3u.write(f"#TOTAL_CHANNELS: {len(КАНАЛЫ)}\n\n")
        
        for id_, _, name in КАНАЛЫ:
            данные = результаты.get(id_, {})
            потоки = данные.get("streams", [])
            
            if not потоки:
                continue
            
            # Выбираем лучший поток для отображения в EXTINF
            лучший = выбрать_лучший_поток(потоки)
            
            f_m3u.write(f'#EXTINF:-1 tvg-id="{id_}" tvg-name="{name}" group-title="Vitrina TV",{name}\n')
            f_m3u.write("#EXTVLCOPT:http-referrer=https://vitrina.tv/\n")
            
            # Записываем ВСЕ потоки (каждый со своими тегами)
            for поток in потоки:
                if поток["type"] == "dash":
                    f_m3u.write("#KODIPROP:inputstreamaddon=inputstream.adaptive\n")
                    f_m3u.write("#KODIPROP:inputstream.adaptive.manifest_type=dash\n")
                f_m3u.write(поток["url"] + "\n")
                f_txt.write(f"{name}|{поток['type']}|{поток['url']}\n")
            
            f_m3u.write("\n")
            channels_with_streams += 1
            total_streams += len(потоки)
    
    # Статистика
    print("\n" + "=" * 70)
    print(f"📊 СТАТИСТИКА СОХРАНЕНИЯ")
    print("=" * 70)
    print(f"✅ Каналов с потоками: {channels_with_streams}/{len(КАНАЛЫ)}")
    print(f"📡 Всего потоков найдено: {total_streams}")
    
    no_stream = [name for _, _, name in КАНАЛЫ 
                 if not результаты.get(_, {}).get("streams")]
    
    if no_stream:
        print(f"❌ Без потока ({len(no_stream)}): {', '.join(no_stream[:10])}")
        if len(no_stream) > 10:
            print(f"   ... и ещё {len(no_stream) - 10}")
    
    print(f"\n📁 M3U файл: {m3u_path}")
    print(f"📁 TXT файл: {txt_path}")
    
    # Генерируем ссылку для GitVerse
    repo = os.environ.get("GITVERSE_REPOSITORY", os.environ.get("GITHUB_REPOSITORY", "user/repo"))
    branch = os.environ.get("GITVERSE_REF_NAME", os.environ.get("GITHUB_REF_NAME", "main"))
    
    raw_url = f"https://gitverse.ru/{repo}/raw/{branch}/{m3u_path.replace(os.sep, '/')}"
    
    with open("VITRINA_URL.txt", "w", encoding="utf-8") as f:
        f.write(raw_url)
    
    print(f"🔗 RAW ссылка: {raw_url}")
    
    return channels_with_streams, m3u_path


async def main():
    """Главная функция"""
    start = time.time()
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║         🚀 VITRINA TV СНИФФЕР v4.0                           ║
║         Сохраняем ВСЕ найденные потоки                       ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    await запустить()
    count, path = сохранить()
    
    elapsed = time.time() - start
    print(f"\n⏱️  Время выполнения: {elapsed:.0f} сек")
    print(f"📊 Каналов сохранено: {count}")


if __name__ == "__main__":
    asyncio.run(main())
