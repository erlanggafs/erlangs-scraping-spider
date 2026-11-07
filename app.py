import base64
import csv
import io
import json
import os
import threading
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from scrapling.fetchers import StealthyFetcher

# ==========================================================
# State Global Spider Crawler
# ==========================================================
CRAWLER_LOCK = threading.Lock()
CRAWLER_STATE = {
    "is_running": False,
    "should_stop": False,
    "keyword": "ijazah jokowi",
    "limit": 20,
    "headless": False,
    "current_page": 0,
    "current_domain": "",
    "current_action": "NEON SPIDER MATRIX STANDBY",
    "progress_percent": 0,
    "unique_domains": 0,
    "logs": [],
    "articles": [],
    "start_time": 0,
    "elapsed_time": 0,
    "done": False,
    "error": None
}


def add_log(message: str, level: str = "info"):
    timestamp = time.strftime("%H:%M:%S")
    with CRAWLER_LOCK:
        CRAWLER_STATE["logs"].append({
            "time": timestamp,
            "text": message,
            "level": level
        })
        if len(CRAWLER_STATE["logs"]) > 150:
            CRAWLER_STATE["logs"].pop(0)


def decode_bing_url(url: str) -> str:
    """Dekode redirect URL Bing ck/a menjadi direct URL tujuan asli."""
    if "bing.com/ck/a?" in url:
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        u_val = params.get("u", [""])[0]
        if u_val.startswith("a1"):
            raw_b64 = u_val[2:]
            raw_b64 += "=" * (-len(raw_b64) % 4)
            try:
                return base64.b64decode(raw_b64).decode("utf-8")
            except Exception:
                pass
    return url


def crawler_worker(keyword: str, total_limit: int, headless: bool):
    global CRAWLER_STATE

    with CRAWLER_LOCK:
        CRAWLER_STATE["is_running"] = True
        CRAWLER_STATE["should_stop"] = False
        CRAWLER_STATE["keyword"] = keyword
        CRAWLER_STATE["limit"] = total_limit
        CRAWLER_STATE["headless"] = headless
        CRAWLER_STATE["current_action"] = "INITIALIZING CYBERNETIC PROTOCOL..."
        CRAWLER_STATE["articles"] = []
        CRAWLER_STATE["logs"] = []
        CRAWLER_STATE["progress_percent"] = 0
        CRAWLER_STATE["unique_domains"] = 0
        CRAWLER_STATE["start_time"] = time.time()
        CRAWLER_STATE["elapsed_time"] = 0
        CRAWLER_STATE["done"] = False
        CRAWLER_STATE["error"] = None

    add_log(f"⚡ [CORE ACTIVATED] Cyber Spider protocol online. Query: '{keyword}'", "neon-cyan")
    add_log(f"🌐 [NEURAL NET] Scanning Search Engine Multi-Domain Matrix...", "neon-purple")
    add_log(f"🎯 [TARGET QUOTA] {total_limit} Dossiers | Stealth Browser: {'ACTIVE' if not headless else 'BACKGROUND'}", "neon-green")

    encoded_query = urllib.parse.quote_plus(keyword)
    seen_urls = set()
    found_domains = set()

    try:
        max_pages = max(3, (total_limit // 8) + 2)

        for page_idx in range(max_pages):
            if CRAWLER_STATE["should_stop"]:
                add_log("🛑 [HALT COMMAND] Cyber Spider terminated by operative.", "warn")
                with CRAWLER_LOCK:
                    CRAWLER_STATE["current_action"] = "CYBER SPIDER MISSION ABORTED"
                break

            offset = (page_idx * 10) + 1
            target_url = f"https://www.bing.com/news/search?q={encoded_query}&first={offset}"
            
            with CRAWLER_LOCK:
                CRAWLER_STATE["current_page"] = page_idx + 1
                CRAWLER_STATE["current_action"] = f"INFILTRATING SECTOR {page_idx + 1} (NODE {offset})..."

            add_log(f"🕸️ [PROBING SECTOR {page_idx + 1}] Target Node {offset}...", "info")

            try:
                response = StealthyFetcher.fetch(
                    target_url,
                    headless=headless,
                    network_idle=True,
                    timeout=30000
                )

                if response.status != 200:
                    add_log(f"⚠️ [FIREWALL ANOMALY] HTTP Status {response.status}. Rerouting...", "warn")
                    continue

                cards = response.css(".news-card")
                if not cards:
                    add_log("ℹ️ [SCAN COMPLETED] No further intelligence packets located.", "info")
                    break

                for c in cards:
                    if CRAWLER_STATE["should_stop"]:
                        break

                    title = c.attrib.get("data-title") or c.attrib.get("title") or (c.css("a.title::text").get() or "").strip()
                    raw_url = c.attrib.get("data-url") or c.attrib.get("url") or c.css("a.title::attr(href)").get() or ""
                    clean_url = decode_bing_url(raw_url)

                    if not title or not clean_url or clean_url in seen_urls:
                        continue
                    seen_urls.add(clean_url)

                    domain = urllib.parse.urlparse(clean_url).netloc.replace("www.", "")
                    author = c.attrib.get("data-author") or domain
                    time_val = c.css("span[aria-label]::attr(aria-label)").get() or (c.css(".source span::text").get() or "").strip()
                    snippet = (c.css(".snippet::text").get() or "").strip()

                    found_domains.add(domain)

                    item_data = {
                        "sumber": author,
                        "domain": domain,
                        "judul": title,
                        "waktu": time_val,
                        "ringkasan": snippet,
                        "url": clean_url
                    }

                    with CRAWLER_LOCK:
                        CRAWLER_STATE["current_domain"] = domain
                        CRAWLER_STATE["current_action"] = f"EXTRACTING INTEL FROM [{domain.upper()}]"
                        CRAWLER_STATE["articles"].append(item_data)
                        total_found = len(CRAWLER_STATE["articles"])
                        CRAWLER_STATE["progress_percent"] = min(100, int((total_found / total_limit) * 100))
                        CRAWLER_STATE["unique_domains"] = len(found_domains)
                        CRAWLER_STATE["elapsed_time"] = round(time.time() - CRAWLER_STATE["start_time"], 1)

                    add_log(f"💎 [INTERCEPTED] [{domain.upper()}] {title[:55]}...", "success")

                    time.sleep(0.15)

                    if len(CRAWLER_STATE["articles"]) >= total_limit:
                        add_log(f"🎯 [MAX QUOTA REACHED] Objective complete ({total_limit} dossiers secure).", "success")
                        with CRAWLER_LOCK:
                            CRAWLER_STATE["current_action"] = "CYBERNETIC OPERATION COMPLETED"
                        break

                if len(CRAWLER_STATE["articles"]) >= total_limit:
                    break

            except Exception as page_err:
                add_log(f"❌ [CYBER ERROR] {str(page_err)}", "error")

        with CRAWLER_LOCK:
            CRAWLER_STATE["progress_percent"] = 100
            CRAWLER_STATE["elapsed_time"] = round(time.time() - CRAWLER_STATE["start_time"], 1)

        add_log(f"🏁 [MISSION SUCCESS] Secured {len(CRAWLER_STATE['articles'])} dossiers across {len(found_domains)} nodes.", "success")

        with open("berita_ijazah_jokowi.json", "w", encoding="utf-8") as f:
            json.dump(CRAWLER_STATE["articles"], f, indent=4, ensure_ascii=False)
        with open("berita_ijazah_jokowi.csv", "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["sumber", "domain", "judul", "waktu", "ringkasan", "url"])
            writer.writeheader()
            writer.writerows(CRAWLER_STATE["articles"])

    except Exception as e:
        add_log(f"💥 [SYSTEM FAILURE] {str(e)}", "error")
        with CRAWLER_LOCK:
            CRAWLER_STATE["error"] = str(e)
            CRAWLER_STATE["current_action"] = "CORE MATRIX FAILURE"
    finally:
        with CRAWLER_LOCK:
            CRAWLER_STATE["is_running"] = False
            CRAWLER_STATE["done"] = True


# ==========================================================
# Frontend HTML/CSS/JS (Fully Responsive Futuristic Neon UI)
# ==========================================================
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>CYBERNETIC SPIDER // NEON CRAWLER MATRIX</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;800;900&family=Rajdhani:wght@500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-void: #03060f;
      --bg-panel: rgba(7, 12, 24, 0.85);
      --neon-cyan: #00f3ff;
      --neon-cyan-glow: 0 0 15px rgba(0, 243, 255, 0.6), 0 0 30px rgba(0, 243, 255, 0.25);
      --neon-pink: #ff0055;
      --neon-pink-glow: 0 0 15px rgba(255, 0, 85, 0.6), 0 0 30px rgba(255, 0, 85, 0.25);
      --neon-green: #00ff88;
      --neon-green-glow: 0 0 15px rgba(0, 255, 136, 0.6), 0 0 30px rgba(0, 255, 136, 0.25);
      --neon-purple: #9d4edd;
      --neon-amber: #ffaa00;
      --border-cyber: rgba(0, 243, 255, 0.25);
      --text-main: #e2f1ff;
      --text-muted: #738ba8;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'Rajdhani', sans-serif;
      background-color: var(--bg-void);
      background-image: 
        radial-gradient(circle at 50% 0%, rgba(0, 243, 255, 0.12) 0%, transparent 60%),
        radial-gradient(circle at 90% 90%, rgba(255, 0, 85, 0.08) 0%, transparent 50%),
        linear-gradient(rgba(0, 243, 255, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 243, 255, 0.03) 1px, transparent 1px);
      background-size: 100% 100%, 100% 100%, 35px 35px, 35px 35px;
      color: var(--text-main);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      overflow-x: hidden;
      letter-spacing: 0.03em;
    }

    /* Scanline effect */
    body::before {
      content: "";
      position: fixed;
      top: 0; left: 0; width: 100%; height: 100%;
      background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.35) 50%);
      background-size: 100% 4px;
      pointer-events: none;
      z-index: 999;
      opacity: 0.35;
    }

    /* HEADER (RESPONSIVE) */
    header {
      background: rgba(3, 7, 18, 0.9);
      backdrop-filter: blur(16px);
      border-bottom: 1px solid var(--border-cyber);
      box-shadow: 0 4px 30px rgba(0, 243, 255, 0.12);
      padding: clamp(0.7rem, 2vw, 1rem) clamp(1rem, 3vw, 2.5rem);
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: sticky;
      top: 0;
      z-index: 50;
      gap: 1rem;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: clamp(0.6rem, 1.5vw, 1rem);
    }

    .brand-core {
      width: clamp(38px, 5vw, 46px);
      height: clamp(38px, 5vw, 46px);
      background: rgba(0, 0, 0, 0.6);
      border: 1px solid var(--neon-cyan);
      box-shadow: var(--neon-cyan-glow);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: clamp(1.3rem, 2.5vw, 1.7rem);
      flex-shrink: 0;
      clip-path: polygon(15% 0%, 100% 0%, 100% 85%, 85% 100%, 0% 100%, 0% 15%);
    }

    .brand h1 {
      font-family: 'Orbitron', sans-serif;
      font-size: clamp(0.95rem, 2.2vw, 1.35rem);
      font-weight: 900;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      background: linear-gradient(135deg, #ffffff 30%, var(--neon-cyan) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      text-shadow: 0 0 20px rgba(0, 243, 255, 0.4);
      white-space: nowrap;
    }

    .brand-sub {
      font-size: clamp(0.62rem, 1.2vw, 0.75rem);
      color: var(--neon-cyan);
      letter-spacing: 0.15em;
      font-weight: 600;
      opacity: 0.8;
      font-family: 'Orbitron', sans-serif;
      display: block;
    }

    .hud-badge {
      font-family: 'Orbitron', sans-serif;
      font-size: clamp(0.68rem, 1.2vw, 0.8rem);
      font-weight: 700;
      padding: clamp(0.35rem, 1vw, 0.45rem) clamp(0.7rem, 1.5vw, 1.1rem);
      border-radius: 4px;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      background: rgba(15, 23, 42, 0.8);
      color: var(--text-muted);
      border: 1px solid rgba(255, 255, 255, 0.15);
      clip-path: polygon(6px 0%, 100% 0%, calc(100% - 6px) 100%, 0% 100%);
      transition: all 0.3s;
      white-space: nowrap;
      flex-shrink: 0;
    }

    .hud-badge.active {
      background: rgba(0, 243, 255, 0.12);
      color: var(--neon-cyan);
      border-color: var(--neon-cyan);
      box-shadow: var(--neon-cyan-glow);
    }

    .hud-dot {
      width: 8px;
      height: 8px;
      background: currentColor;
      box-shadow: 0 0 8px currentColor;
    }
    .hud-badge.active .hud-dot {
      animation: pulseNeon 1s infinite alternate;
    }
    @keyframes pulseNeon {
      from { transform: scale(0.8); opacity: 0.5; }
      to { transform: scale(1.3); opacity: 1; }
    }

    /* MAIN CONTAINER (FLUID GRID) */
    main {
      flex: 1;
      max-width: 1480px;
      width: 100%;
      margin: 0 auto;
      padding: clamp(1rem, 2.5vw, 2rem);
      display: grid;
      grid-template-columns: 360px 1fr;
      gap: clamp(1rem, 2vw, 2rem);
    }

    @media (max-width: 1024px) {
      main {
        grid-template-columns: 1fr;
      }
    }

    /* CYBER PANEL (RESPONSIVE) */
    .cyber-panel {
      background: var(--bg-panel);
      backdrop-filter: blur(20px);
      border: 1px solid var(--border-cyber);
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.7);
      border-radius: 12px;
      padding: clamp(1.1rem, 2vw, 1.6rem);
      position: relative;
      clip-path: polygon(0 0, calc(100% - 16px) 0, 100% 16px, 100% 100%, 16px 100%, 0 calc(100% - 16px));
      height: fit-content;
    }
    .cyber-panel::before {
      content: "";
      position: absolute;
      top: 0; right: 0;
      width: 20px; height: 20px;
      border-top: 2px solid var(--neon-cyan);
      border-right: 2px solid var(--neon-cyan);
      box-shadow: var(--neon-cyan-glow);
    }
    .cyber-panel::after {
      content: "";
      position: absolute;
      bottom: 0; left: 0;
      width: 20px; height: 20px;
      border-bottom: 2px solid var(--neon-cyan);
      border-left: 2px solid var(--neon-cyan);
      box-shadow: var(--neon-cyan-glow);
    }

    .panel-header {
      font-family: 'Orbitron', sans-serif;
      font-size: clamp(0.9rem, 1.8vw, 1.05rem);
      font-weight: 800;
      color: var(--neon-cyan);
      text-transform: uppercase;
      letter-spacing: 0.12em;
      margin-bottom: 1.25rem;
      display: flex;
      align-items: center;
      gap: 0.6rem;
      border-bottom: 1px solid rgba(0, 243, 255, 0.2);
      padding-bottom: 0.7rem;
      text-shadow: 0 0 10px rgba(0, 243, 255, 0.4);
    }

    .form-group {
      margin-bottom: 1.2rem;
    }

    label {
      display: block;
      font-family: 'Orbitron', sans-serif;
      font-size: 0.72rem;
      font-weight: 700;
      color: var(--neon-cyan);
      letter-spacing: 0.1em;
      text-transform: uppercase;
      margin-bottom: 0.45rem;
    }

    input[type="text"], input[type="number"] {
      width: 100%;
      background: rgba(3, 7, 18, 0.9);
      border: 1px solid rgba(0, 243, 255, 0.3);
      border-radius: 6px;
      padding: clamp(0.7rem, 1.5vw, 0.85rem) 1rem;
      color: #ffffff;
      font-size: 1rem;
      font-family: 'Rajdhani', sans-serif;
      font-weight: 600;
      letter-spacing: 0.05em;
      outline: none;
      transition: all 0.25s ease;
      min-height: 44px;
    }
    input[type="text"]:focus, input[type="number"]:focus {
      border-color: var(--neon-cyan);
      box-shadow: var(--neon-cyan-glow);
      background: rgba(5, 12, 30, 0.95);
    }

    .neon-info-box {
      background: rgba(157, 78, 221, 0.09);
      border: 1px dashed var(--neon-purple);
      padding: 0.8rem;
      border-radius: 8px;
      font-size: clamp(0.78rem, 1.4vw, 0.85rem);
      color: #e0aaff;
      line-height: 1.45;
      box-shadow: inset 0 0 15px rgba(157, 78, 221, 0.12);
    }

    .toggle-cyber {
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: rgba(3, 7, 18, 0.8);
      border: 1px solid rgba(0, 243, 255, 0.2);
      padding: 0.75rem 0.9rem;
      border-radius: 8px;
      gap: 0.8rem;
    }
    .toggle-title {
      font-weight: 700;
      font-size: clamp(0.85rem, 1.5vw, 0.92rem);
      color: var(--text-main);
    }
    .toggle-desc {
      font-size: 0.72rem;
      color: var(--text-muted);
    }

    /* BUTTONS */
    .btn-cyber {
      width: 100%;
      padding: clamp(0.8rem, 1.8vw, 0.95rem);
      font-family: 'Orbitron', sans-serif;
      font-size: clamp(0.78rem, 1.5vw, 0.88rem);
      font-weight: 900;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.6rem;
      border: none;
      position: relative;
      clip-path: polygon(10px 0%, 100% 0%, calc(100% - 10px) 100%, 0% 100%);
      transition: all 0.25s ease;
      min-height: 46px;
    }

    .btn-launch {
      background: linear-gradient(135deg, #00ff88 0%, #00b4d8 100%);
      color: #03060f;
      box-shadow: 0 0 25px rgba(0, 255, 136, 0.4);
    }
    .btn-launch:hover:not(:disabled) {
      filter: brightness(1.15);
      transform: translateY(-2px);
      box-shadow: 0 0 35px rgba(0, 255, 136, 0.7);
    }

    .btn-abort {
      background: linear-gradient(135deg, #ff0055 0%, #990033 100%);
      color: #ffffff;
      margin-top: 0.7rem;
      box-shadow: 0 0 20px rgba(255, 0, 85, 0.35);
    }
    .btn-abort:hover:not(:disabled) {
      filter: brightness(1.2);
      box-shadow: 0 0 30px rgba(255, 0, 85, 0.6);
    }

    .btn-cyber:disabled {
      opacity: 0.35;
      cursor: not-allowed;
      transform: none !important;
      box-shadow: none !important;
    }

    /* =========================================================
       SPIDER LIVE HUD RADAR CANVAS (RESPONSIVE)
       ========================================================= */
    .radar-stage {
      background: rgba(3, 7, 18, 0.94);
      border: 1px solid var(--border-cyber);
      border-radius: 12px;
      overflow: hidden;
      margin-bottom: clamp(1rem, 2vw, 1.5rem);
      box-shadow: var(--neon-cyan-glow), inset 0 0 30px rgba(0, 243, 255, 0.08);
      position: relative;
      clip-path: polygon(0 0, calc(100% - 14px) 0, 100% 14px, 100% 100%, 14px 100%, 0 calc(100% - 14px));
    }
    .radar-stage-bar {
      background: rgba(0, 243, 255, 0.08);
      border-bottom: 1px solid rgba(0, 243, 255, 0.25);
      padding: 0.65rem clamp(0.8rem, 2vw, 1.3rem);
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-family: 'Orbitron', sans-serif;
      font-size: clamp(0.7rem, 1.5vw, 0.8rem);
      font-weight: 700;
      letter-spacing: 0.08em;
      gap: 0.5rem;
      flex-wrap: wrap;
    }
    .radar-action-ticker {
      color: var(--neon-cyan);
      font-family: 'JetBrains Mono', monospace;
      font-size: clamp(0.68rem, 1.4vw, 0.78rem);
      text-shadow: 0 0 8px var(--neon-cyan);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      max-width: 100%;
    }

    .canvas-hud-container {
      width: 100%;
      height: clamp(210px, 32vw, 275px);
      position: relative;
      background: 
        radial-gradient(circle at 50% 50%, rgba(0, 243, 255, 0.07) 0%, rgba(3, 6, 15, 0.98) 75%),
        linear-gradient(rgba(0, 243, 255, 0.05) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 243, 255, 0.05) 1px, transparent 1px);
      background-size: 100% 100%, 25px 25px, 25px 25px;
    }

    canvas {
      display: block;
      width: 100%;
      height: 100%;
    }

    /* STATS HUD MATRIX (RESPONSIVE GRID) */
    .hud-stats-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: clamp(0.7rem, 1.5vw, 1.1rem);
      margin-bottom: clamp(1rem, 2vw, 1.5rem);
    }

    @media (max-width: 720px) {
      .hud-stats-grid {
        grid-template-columns: repeat(2, 1fr);
      }
    }

    .hud-stat-box {
      background: rgba(7, 14, 28, 0.8);
      border: 1px solid rgba(0, 243, 255, 0.25);
      border-radius: 8px;
      padding: clamp(0.75rem, 1.5vw, 1.1rem);
      position: relative;
      transition: all 0.3s;
    }
    .hud-stat-box:hover {
      border-color: var(--neon-cyan);
      box-shadow: 0 0 20px rgba(0, 243, 255, 0.2);
    }
    .hud-stat-label {
      font-family: 'Orbitron', sans-serif;
      font-size: clamp(0.62rem, 1.2vw, 0.68rem);
      font-weight: 800;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.1em;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .hud-stat-num {
      font-family: 'Orbitron', sans-serif;
      font-size: clamp(1.35rem, 3vw, 1.8rem);
      font-weight: 900;
      color: #ffffff;
      margin-top: 0.25rem;
      text-shadow: 0 0 15px currentColor;
      line-height: 1.1;
    }

    /* PROGRESS HUD */
    .hud-progress-card {
      background: rgba(7, 14, 28, 0.8);
      border: 1px solid rgba(0, 243, 255, 0.2);
      border-radius: 8px;
      padding: clamp(0.8rem, 1.5vw, 1.1rem);
      margin-bottom: clamp(1rem, 2vw, 1.5rem);
    }
    .hud-progress-head {
      display: flex;
      justify-content: space-between;
      font-family: 'Orbitron', sans-serif;
      font-size: clamp(0.72rem, 1.5vw, 0.8rem);
      font-weight: 700;
      color: var(--neon-cyan);
      letter-spacing: 0.08em;
      margin-bottom: 0.5rem;
    }
    .hud-progress-track {
      height: 10px;
      background: rgba(3, 7, 18, 0.95);
      border: 1px solid rgba(0, 243, 255, 0.3);
      border-radius: 3px;
      overflow: hidden;
      padding: 2px;
    }
    .hud-progress-fill {
      height: 100%;
      background: linear-gradient(90deg, #00f3ff, #ff0055);
      width: 0%;
      box-shadow: 0 0 12px var(--neon-cyan);
      transition: width 0.3s ease;
    }

    /* CYBER TERMINAL (RESPONSIVE HEIGHT) */
    .cyber-terminal {
      background: rgba(3, 6, 14, 0.95);
      border: 1px solid rgba(0, 255, 136, 0.3);
      border-radius: 8px;
      font-family: 'JetBrains Mono', monospace;
      font-size: clamp(0.72rem, 1.4vw, 0.82rem);
      height: clamp(140px, 20vw, 180px);
      overflow-y: auto;
      padding: 0.85rem;
      margin-bottom: clamp(1rem, 2vw, 1.5rem);
      box-shadow: inset 0 0 20px rgba(0, 255, 136, 0.05);
    }
    .terminal-bar {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      border-bottom: 1px solid rgba(0, 255, 136, 0.2);
      padding-bottom: 0.4rem;
      margin-bottom: 0.6rem;
      color: var(--neon-green);
      font-size: 0.68rem;
      font-weight: 700;
      letter-spacing: 0.08em;
    }
    .log-item {
      display: flex;
      gap: 0.6rem;
      line-height: 1.5;
      word-break: break-word;
    }
    .log-timestamp { color: #52796f; font-weight: 600; flex-shrink: 0; }
    .log-msg { color: #d8f3dc; }
    .log-msg.neon-cyan { color: var(--neon-cyan); text-shadow: 0 0 6px var(--neon-cyan); }
    .log-msg.neon-green, .log-msg.success { color: var(--neon-green); text-shadow: 0 0 6px var(--neon-green); }
    .log-msg.neon-purple { color: #c77dff; }
    .log-msg.warn { color: var(--neon-amber); }
    .log-msg.error { color: var(--neon-pink); text-shadow: 0 0 6px var(--neon-pink); }

    /* DOSSIER RESULTS (CARDS) */
    .dossier-panel {
      background: var(--bg-panel);
      backdrop-filter: blur(20px);
      border: 1px solid var(--border-cyber);
      border-radius: 12px;
      padding: clamp(1rem, 2vw, 1.6rem);
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.7);
    }
    .dossier-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.2rem;
      border-bottom: 1px solid rgba(0, 243, 255, 0.2);
      padding-bottom: 0.8rem;
      gap: 0.8rem;
      flex-wrap: wrap;
    }
    .dossier-title {
      font-family: 'Orbitron', sans-serif;
      font-size: clamp(0.95rem, 1.8vw, 1.1rem);
      font-weight: 800;
      color: var(--neon-cyan);
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .export-btns {
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
    }

    .btn-export-neon {
      padding: 0.45rem 0.85rem;
      border-radius: 4px;
      font-family: 'Orbitron', sans-serif;
      font-size: clamp(0.68rem, 1.3vw, 0.75rem);
      font-weight: 800;
      background: rgba(0, 243, 255, 0.08);
      color: var(--neon-cyan);
      border: 1px solid var(--neon-cyan);
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      letter-spacing: 0.06em;
      transition: all 0.25s;
      min-height: 36px;
    }
    .btn-export-neon:hover {
      background: var(--neon-cyan);
      color: #03060f;
      box-shadow: var(--neon-cyan-glow);
    }

    .article-dossier {
      background: rgba(4, 9, 20, 0.85);
      border: 1px solid rgba(0, 243, 255, 0.2);
      border-left: 4px solid var(--neon-cyan);
      border-radius: 6px;
      padding: clamp(0.9rem, 1.8vw, 1.2rem);
      margin-bottom: 0.9rem;
      transition: all 0.25s ease;
      position: relative;
    }
    .article-dossier:hover {
      border-color: var(--neon-cyan);
      border-left-color: var(--neon-pink);
      transform: translateX(3px);
      box-shadow: 0 4px 20px rgba(0, 243, 255, 0.2);
    }

    .dossier-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 0.5rem;
      gap: 0.5rem;
      flex-wrap: wrap;
    }
    .badge-hub {
      display: flex;
      align-items: center;
      gap: 0.45rem;
      flex-wrap: wrap;
    }
    .tag-author {
      font-family: 'Orbitron', sans-serif;
      font-size: 0.65rem;
      font-weight: 800;
      padding: 0.2rem 0.55rem;
      border-radius: 3px;
      background: rgba(255, 0, 85, 0.15);
      color: var(--neon-pink);
      border: 1px solid var(--neon-pink);
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }
    .tag-domain {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.7rem;
      font-weight: 600;
      padding: 0.2rem 0.5rem;
      border-radius: 3px;
      background: rgba(0, 255, 136, 0.12);
      color: var(--neon-green);
      border: 1px solid rgba(0, 255, 136, 0.4);
    }
    .dossier-time {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.72rem;
      color: var(--text-muted);
      white-space: nowrap;
    }
    .dossier-heading {
      font-size: clamp(0.95rem, 2vw, 1.15rem);
      font-weight: 700;
      color: #ffffff;
      text-decoration: none;
      display: block;
      margin-bottom: 0.4rem;
      line-height: 1.35;
      transition: color 0.2s;
      word-break: break-word;
    }
    .dossier-heading:hover {
      color: var(--neon-cyan);
      text-shadow: 0 0 10px rgba(0, 243, 255, 0.6);
    }
    .dossier-desc {
      font-size: clamp(0.82rem, 1.6vw, 0.9rem);
      color: #9cb1c9;
      line-height: 1.5;
      word-break: break-word;
    }

    .empty-hud {
      text-align: center;
      padding: 2.5rem 1rem;
      color: var(--text-muted);
      font-family: 'Orbitron', sans-serif;
      font-size: 0.8rem;
      letter-spacing: 0.08em;
    }

    /* ULTRA-SMALL MOBILE SCREEN OPTIMIZATION */
    @media (max-width: 480px) {
      header {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.6rem;
      }
      .hud-badge {
        align-self: flex-start;
      }
      .dossier-bar {
        flex-direction: column;
        align-items: flex-start;
      }
      .export-btns {
        width: 100%;
      }
      .btn-export-neon {
        flex: 1;
        justify-content: center;
      }
    }
  </style>
</head>
<body>

  <!-- HEADER (RESPONSIVE) -->
  <header>
    <div class="brand">
      <div class="brand-core">🕷️</div>
      <div>
        <h1>Erlangs Scraping Spider</h1>
        <div class="brand-sub">CYBERNETIC CRAWLER</div>
      </div>
    </div>
    <div id="statusBadge" class="hud-badge">
      <span class="hud-dot"></span>
      <span id="statusText">MATRIX STANDBY</span>
    </div>
  </header>

  <!-- MAIN -->
  <main>
    <!-- CONTROL COCKPIT -->
    <div class="cyber-panel">
      <div class="panel-header">
        <span>⚡ MISSION CONTROLLER</span>
      </div>

      <div class="form-group">
        <label for="keywordInput">Intelligence Query (Keyword)</label>
        <input type="text" id="keywordInput" value="ijazah jokowi" placeholder="ENTER TARGET QUERY...">
      </div>

      <div class="form-group">
        <label for="limitInput">Target Quota (Max Articles)</label>
        <input type="number" id="limitInput" value="20" min="1" max="100">
      </div>

      <div class="form-group">
        <label>Network Coverage</label>
        <div class="neon-info-box">
          🌐 <strong>SEARCH ENGINE MULTI-DOMAIN MATRIX</strong><br>
          Autonomous deep web crawler interrogates global search engine nodes to intercept news across all media (Kompas, Detik, Liputan6, CNN, Tempo, etc).
        </div>
      </div>

      <div class="form-group">
        <div class="toggle-cyber">
          <div>
            <div class="toggle-title">Chromium Stealth GUI</div>
            <div class="toggle-desc">Visualize real browser viewport</div>
          </div>
          <input type="checkbox" id="checkGui" checked style="transform: scale(1.35); accent-color: var(--neon-cyan); cursor: pointer;">
        </div>
      </div>

      <button id="startBtn" class="btn-cyber btn-launch" onclick="startCrawler()">
        <span>🚀 RUN SEARCHING</span>
      </button>

      <button id="stopBtn" class="btn-cyber btn-abort" onclick="stopCrawler()" disabled>
        <span>🛑 ABORT MISSION</span>
      </button>
    </div>

    <!-- HUD DASHBOARD & LIVE CANVAS RADAR -->
    <div>
      <!-- LIVE SPIDER HUD RADAR CANVAS -->
      <div class="radar-stage">
        <div class="radar-stage-bar">
          <div style="display:flex; align-items:center; gap:0.5rem; color:var(--neon-cyan);">
            <span>📡 TACTICAL SPIDER RADAR</span>
          </div>
          <span id="spiderActionText" class="radar-action-ticker">SYSTEM ARMED // AWAITING DISPATCH</span>
        </div>
        <div class="canvas-hud-container">
          <canvas id="spiderCanvas"></canvas>
        </div>
      </div>

      <!-- STATS HUD -->
      <div class="hud-stats-grid">
        <div class="hud-stat-box">
          <div class="hud-stat-label">Dossiers</div>
          <div id="statTotal" class="hud-stat-num" style="color: var(--neon-green);">0</div>
        </div>
        <div class="hud-stat-box">
          <div class="hud-stat-label">Quota</div>
          <div id="statLimit" class="hud-stat-num" style="color: var(--neon-cyan);">20</div>
        </div>
        <div class="hud-stat-box">
          <div class="hud-stat-label">Nodes</div>
          <div id="statDomain" class="hud-stat-num" style="color: var(--neon-purple);">0</div>
        </div>
        <div class="hud-stat-box">
          <div class="hud-stat-label">Elapsed</div>
          <div id="statTime" class="hud-stat-num" style="color: var(--neon-pink);">0.0s</div>
        </div>
      </div>

      <!-- PROGRESS -->
      <div class="hud-progress-card">
        <div class="hud-progress-head">
          <span>INFILTRATION PROGRESS</span>
          <span id="progressText">0%</span>
        </div>
        <div class="hud-progress-track">
          <div id="progressBar" class="hud-progress-fill"></div>
        </div>
      </div>

      <!-- TERMINAL CONSOLE -->
      <div class="cyber-terminal" id="terminalLog">
        <div class="terminal-bar">
          <span>⚡ NEURAL LOG STREAM // TTY0</span>
        </div>
        <div id="logLines">
          <div class="log-item">
            <span class="log-timestamp">[00:00:00]</span>
            <span class="log-msg neon-cyan">Neural network online. Press 'Run Searching' to deploy the spider.</span>
          </div>
        </div>
      </div>

      <!-- DOSSIER ARCHIVE LIST -->
      <div class="dossier-panel">
        <div class="dossier-bar">
          <div class="dossier-title">📁 INTERCEPTED INTEL (<span id="countText">0</span>)</div>
          <div class="export-btns">
            <a href="/api/download/csv" class="btn-export-neon">💾 CSV</a>
            <a href="/api/download/json" class="btn-export-neon">💾 JSON</a>
          </div>
        </div>

        <div id="articlesList">
          <div class="empty-hud">
            <div>🕸️ AWAITING TARGET INTERCEPTION</div>
            <p style="margin-top: 0.4rem; font-size: 0.72rem; color: #536b85;">NO ENCRYPTED INTELLIGENCE PACKETS RECEIVED YET.</p>
          </div>
        </div>
      </div>
    </div>
  </main>

  <script>
    let pollInterval = null;
    let globalIsRunning = false;

    // ==========================================================
    // RESPONSIVE HIGH-TECH NEON SPIDER & RADAR CANVAS ENGINE
    // ==========================================================
    const canvas = document.getElementById('spiderCanvas');
    const ctx = canvas.getContext('2d');
    let width, height;

    function resizeCanvas() {
      const rect = canvas.parentElement.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      width = rect.width;
      height = rect.height;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.scale(dpr, dpr);
    }
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

    const domainNodes = [
      { name: 'SEARCH CORE', x: 0.5, y: 0.5, active: true },
      { name: 'detik.com', x: 0.22, y: 0.28, active: false },
      { name: 'kompas.com', x: 0.78, y: 0.25, active: false },
      { name: 'liputan6.com', x: 0.16, y: 0.75, active: false },
      { name: 'cnnindonesia.com', x: 0.84, y: 0.72, active: false },
      { name: 'tempo.co', x: 0.36, y: 0.16, active: false },
      { name: 'viva.co.id', x: 0.64, y: 0.84, active: false }
    ];

    const spider = {
      x: width * 0.5,
      y: height * 0.5,
      targetX: width * 0.5,
      targetY: height * 0.5,
      angle: 0,
      legPhase: 0,
      sweepAngle: 0,
      silkOriginX: width * 0.5,
      silkOriginY: 0
    };

    let laserBeams = [];

    function triggerLaserPulse(fromNode, toSpider) {
      laserBeams.push({
        startX: fromNode.x * width,
        startY: fromNode.y * height,
        progress: 0,
        speed: 0.05 + Math.random() * 0.03
      });
    }

    function drawNeonWeb() {
      const cx = width * 0.5;
      const cy = height * 0.5;
      const isMobile = width < 480;

      // Concentric Radar Rings
      for (let r = 35; r < Math.max(width, height); r += 45) {
        ctx.strokeStyle = 'rgba(0, 243, 255, 0.06)';
        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.stroke();
      }

      // Radar Crosshair
      ctx.strokeStyle = 'rgba(0, 243, 255, 0.1)';
      ctx.beginPath();
      ctx.moveTo(cx, 0); ctx.lineTo(cx, height);
      ctx.moveTo(0, cy); ctx.lineTo(width, cy);
      ctx.stroke();

      // Sweeping Radar Beam
      if (globalIsRunning) {
        spider.sweepAngle += 0.04;
        const grad = ctx.createRadialGradient(cx, cy, 10, cx, cy, 260);
        grad.addColorStop(0, 'rgba(0, 243, 255, 0.25)');
        grad.addColorStop(1, 'rgba(0, 243, 255, 0)');

        ctx.save();
        ctx.translate(cx, cy);
        ctx.rotate(spider.sweepAngle);
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.arc(0, 0, 260, 0, 0.45);
        ctx.closePath();
        ctx.fillStyle = grad;
        ctx.fill();
        ctx.restore();
      }

      // Neon Web Threads
      ctx.lineWidth = 1.1;
      for (let i = 0; i < domainNodes.length; i++) {
        for (let j = i + 1; j < domainNodes.length; j++) {
          const n1 = domainNodes[i];
          const n2 = domainNodes[j];
          ctx.strokeStyle = 'rgba(157, 78, 221, 0.2)';
          ctx.beginPath();
          ctx.moveTo(n1.x * width, n1.y * height);
          ctx.lineTo(n2.x * width, n2.y * height);
          ctx.stroke();
        }
      }

      // Laser Silk Line
      ctx.strokeStyle = 'rgba(0, 243, 255, 0.6)';
      ctx.shadowColor = '#00f3ff';
      ctx.shadowBlur = 8;
      ctx.lineWidth = 1.6;
      ctx.beginPath();
      ctx.moveTo(spider.silkOriginX, spider.silkOriginY);
      ctx.lineTo(spider.x, spider.y);
      ctx.stroke();
      ctx.shadowBlur = 0;

      // Draw Nodes
      domainNodes.forEach(node => {
        const nx = node.x * width;
        const ny = node.y * height;

        if (node.active) {
          ctx.fillStyle = 'rgba(0, 255, 136, 0.25)';
          ctx.beginPath();
          ctx.arc(nx, ny, isMobile ? 12 : 18, 0, Math.PI * 2);
          ctx.fill();

          ctx.fillStyle = '#00ff88';
          ctx.shadowColor = '#00ff88';
          ctx.shadowBlur = 12;
        } else {
          ctx.fillStyle = 'rgba(0, 243, 255, 0.4)';
          ctx.shadowBlur = 0;
        }

        ctx.beginPath();
        ctx.arc(nx, ny, node.name.includes('CORE') ? (isMobile ? 6 : 8) : (isMobile ? 4 : 5), 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;

        // Label
        const fontSize = isMobile ? '9px' : '11px';
        ctx.font = `700 ${fontSize} "Orbitron", sans-serif`;
        ctx.fillStyle = node.active ? '#00ff88' : '#738ba8';
        ctx.textAlign = 'center';
        ctx.fillText(node.name, nx, ny + (isMobile ? 13 : 17));
      });

      // Flying Laser Energy Packets
      for (let i = laserBeams.length - 1; i >= 0; i--) {
        const b = laserBeams[i];
        b.progress += b.speed;
        const curX = b.startX + (spider.x - b.startX) * b.progress;
        const curY = b.startY + (spider.y - b.startY) * b.progress;

        ctx.fillStyle = '#ff0055';
        ctx.shadowColor = '#ff0055';
        ctx.shadowBlur = 12;
        ctx.beginPath();
        ctx.arc(curX, curY, isMobile ? 3 : 4, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;

        if (b.progress >= 1) laserBeams.splice(i, 1);
      }
    }

    function drawNeonCyberSpider() {
      const isMobile = width < 480;
      const scale = isMobile ? 0.75 : 1;

      ctx.save();
      ctx.translate(spider.x, spider.y);
      ctx.rotate(spider.angle);
      ctx.scale(scale, scale);

      // Spider Targeting Crosshair
      if (globalIsRunning) {
        ctx.strokeStyle = 'rgba(0, 243, 255, 0.6)';
        ctx.shadowColor = '#00f3ff';
        ctx.shadowBlur = 8;
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.arc(0, 0, 36, 0, Math.PI * 2);
        ctx.stroke();

        ctx.strokeStyle = '#ff0055';
        ctx.shadowColor = '#ff0055';
        ctx.beginPath();
        ctx.moveTo(-42, 0); ctx.lineTo(-30, 0);
        ctx.moveTo(30, 0); ctx.lineTo(42, 0);
        ctx.moveTo(0, -42); ctx.lineTo(0, -30);
        ctx.moveTo(0, 30); ctx.lineTo(0, 42);
        ctx.stroke();
        ctx.shadowBlur = 0;
      }

      // 8 Articulated Cyber Legs
      const legCount = 4;
      for (let side = -1; side <= 1; side += 2) {
        for (let i = 0; i < legCount; i++) {
          const baseAngle = (i * 0.28) + 0.32;
          const legMotion = globalIsRunning ? Math.sin(spider.legPhase + i * 1.4) * 0.42 : 0;
          
          const angle1 = side * (baseAngle + legMotion);
          const jointX = Math.cos(angle1) * (18 + i * 2);
          const jointY = Math.sin(angle1) * (18 + i * 2);

          const tipAngle = angle1 + side * 0.6;
          const tipX = jointX + Math.cos(tipAngle) * (22 + i * 3);
          const tipY = jointY + Math.sin(tipAngle) * (22 + i * 3);

          ctx.strokeStyle = '#00f3ff';
          ctx.shadowColor = '#00f3ff';
          ctx.shadowBlur = globalIsRunning ? 8 : 2;
          ctx.lineWidth = 2.4;
          ctx.lineCap = 'round';

          ctx.beginPath();
          ctx.moveTo(0, (i - 1.5) * 4);
          ctx.lineTo(jointX, jointY);
          ctx.lineTo(tipX, tipY);
          ctx.stroke();

          ctx.fillStyle = '#ff0055';
          ctx.shadowColor = '#ff0055';
          ctx.shadowBlur = 5;
          ctx.beginPath();
          ctx.arc(jointX, jointY, 2.2, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      // Abdomen
      ctx.fillStyle = '#030814';
      ctx.strokeStyle = '#00f3ff';
      ctx.lineWidth = 2;
      ctx.shadowColor = '#00f3ff';
      ctx.shadowBlur = 12;

      ctx.beginPath();
      ctx.ellipse(0, 9, 13, 17, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();

      // Reactor Core
      ctx.fillStyle = globalIsRunning ? '#ff0055' : '#00ff88';
      ctx.shadowColor = ctx.fillStyle;
      ctx.shadowBlur = 15;
      ctx.beginPath();
      ctx.arc(0, 9, 5, 0, Math.PI * 2);
      ctx.fill();

      // Cephalothorax
      ctx.fillStyle = '#0a1428';
      ctx.strokeStyle = '#ff0055';
      ctx.lineWidth = 1.8;
      ctx.shadowColor = '#ff0055';
      ctx.shadowBlur = 8;
      ctx.beginPath();
      ctx.ellipse(0, -9, 9, 9, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();

      // 4 Cyber Eyes
      ctx.fillStyle = globalIsRunning ? '#ff0055' : '#00f3ff';
      ctx.shadowColor = ctx.fillStyle;
      ctx.shadowBlur = 8;

      ctx.beginPath();
      ctx.arc(-3.5, -13, 1.8, 0, Math.PI * 2);
      ctx.arc(3.5, -13, 1.8, 0, Math.PI * 2);
      ctx.arc(-1.5, -16, 1.2, 0, Math.PI * 2);
      ctx.arc(1.5, -16, 1.2, 0, Math.PI * 2);
      ctx.fill();

      ctx.restore();
    }

    function animate() {
      ctx.clearRect(0, 0, width, height);

      spider.silkOriginX = width * 0.5;

      if (globalIsRunning) {
        spider.legPhase += 0.22;

        const dx = spider.targetX - spider.x;
        const dy = spider.targetY - spider.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist > 5) {
          spider.angle = Math.atan2(dy, dx) + Math.PI / 2;
          spider.x += dx * 0.055;
          spider.y += dy * 0.055;
        } else {
          const targetNode = domainNodes[Math.floor(Math.random() * domainNodes.length)];
          spider.targetX = targetNode.x * width + (Math.random() * 30 - 15);
          spider.targetY = targetNode.y * height + (Math.random() * 30 - 15);
          triggerLaserPulse(targetNode, spider);
        }
      } else {
        const homeX = width * 0.5;
        const homeY = height * 0.5;
        spider.x += (homeX - spider.x) * 0.05;
        spider.y += (homeY - spider.y) * 0.05;
        spider.angle += (0 - spider.angle) * 0.05;
      }

      drawNeonWeb();
      drawNeonCyberSpider();

      requestAnimationFrame(animate);
    }
    animate();

    // ==========================================================
    // API CONTROLLER
    // ==========================================================
    async function startCrawler() {
      const keyword = document.getElementById('keywordInput').value.trim();
      const limit = parseInt(document.getElementById('limitInput').value) || 20;
      const isGui = document.getElementById('checkGui').checked;

      if (!keyword) {
        alert('PLEASE SPECIFY TARGET QUERY!');
        return;
      }

      document.getElementById('startBtn').disabled = true;
      document.getElementById('stopBtn').disabled = false;
      document.getElementById('statLimit').innerText = limit;
      document.getElementById('articlesList').innerHTML = '<div class="empty-hud"><div>⚡ INFILTRATING MULTI-DOMAIN MATRIX...</div></div>';

      try {
        const res = await fetch('/api/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            keyword: keyword,
            limit: limit,
            headless: !isGui
          })
        });
        const data = await res.json();
        if (data.status === 'started') {
          globalIsRunning = true;
          startPolling();
        }
      } catch (err) {
        alert('MISSION FAILED TO LAUNCH: ' + err);
        document.getElementById('startBtn').disabled = false;
        document.getElementById('stopBtn').disabled = true;
      }
    }

    async function stopCrawler() {
      await fetch('/api/stop', { method: 'POST' });
      document.getElementById('stopBtn').disabled = true;
    }

    function startPolling() {
      if (pollInterval) clearInterval(pollInterval);
      pollInterval = setInterval(fetchStatus, 700);
    }

    async function fetchStatus() {
      try {
        const res = await fetch('/api/status');
        const state = await res.json();

        globalIsRunning = state.is_running;

        const badge = document.getElementById('statusBadge');
        const badgeText = document.getElementById('statusText');
        const actionText = document.getElementById('spiderActionText');

        if (state.is_running) {
          badge.classList.add('active');
          badgeText.innerText = 'MISSION ACTIVE // NODE ' + (state.current_page || 1);
          actionText.innerText = state.current_action || 'SCANNING NEURAL MATRIX...';

          if (state.current_domain) {
            domainNodes.forEach(node => {
              node.active = state.current_domain.includes(node.name) || node.name.includes('CORE');
            });
          }
        } else {
          badge.classList.remove('active');
          badgeText.innerText = state.done ? 'OPERATION CONCLUDED' : 'MATRIX STANDBY';
          actionText.innerText = state.done ? '🎉 ALL INTELLIGENCE PACKETS SECURED' : 'SYSTEM ARMED // AWAITING DISPATCH';
          document.getElementById('startBtn').disabled = false;
          document.getElementById('stopBtn').disabled = true;

          domainNodes.forEach(node => node.active = false);

          if (state.done && pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
          }
        }

        document.getElementById('statTotal').innerText = state.articles.length;
        document.getElementById('statDomain').innerText = state.unique_domains || 0;
        document.getElementById('statTime').innerText = (state.elapsed_time || 0) + 's';

        const percent = state.progress_percent || 0;
        document.getElementById('progressText').innerText = percent + '%';
        document.getElementById('progressBar').style.width = percent + '%';

        renderLogs(state.logs);
        renderArticles(state.articles);

      } catch (e) {
        console.error('Telemetry error:', e);
      }
    }

    function renderLogs(logs) {
      if (!logs || logs.length === 0) return;
      const container = document.getElementById('logLines');
      container.innerHTML = logs.map(l => `
        <div class="log-item">
          <span class="log-timestamp">[${l.time}]</span>
          <span class="log-msg ${l.level}">${escapeHtml(l.text)}</span>
        </div>
      `).join('');
      const term = document.getElementById('terminalLog');
      term.scrollTop = term.scrollHeight;
    }

    function renderArticles(articles) {
      document.getElementById('countText').innerText = articles.length;
      if (!articles || articles.length === 0) return;
      
      const container = document.getElementById('articlesList');
      container.innerHTML = articles.map(a => `
        <div class="article-dossier">
          <div class="dossier-top">
            <div class="badge-hub">
              <span class="tag-author">${escapeHtml(a.sumber || 'INTEL')}</span>
              <span class="tag-domain">${escapeHtml(a.domain || 'WEB')}</span>
            </div>
            <span class="dossier-time">${escapeHtml(a.waktu || '')}</span>
          </div>
          <a href="${escapeHtml(a.url)}" target="_blank" class="dossier-heading">${escapeHtml(a.judul)}</a>
          <div class="dossier-desc">${escapeHtml(a.ringkasan || '')}</div>
        </div>
      `).join('');
    }

    function escapeHtml(str) {
      if (!str) return '';
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }

    fetchStatus();
  </script>
</body>
</html>
"""


# ==========================================================
# HTTP Request Handler
# ==========================================================
class SpiderRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)

        if url.path == "/" or url.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))

        elif url.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            with CRAWLER_LOCK:
                resp = json.dumps(CRAWLER_STATE).encode("utf-8")
            self.wfile.write(resp)

        elif url.path == "/api/download/csv":
            with CRAWLER_LOCK:
                articles = list(CRAWLER_STATE["articles"])

            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=["sumber", "domain", "judul", "waktu", "ringkasan", "url"])
            writer.writeheader()
            writer.writerows(articles)

            data = output.getvalue().encode("utf-8-sig")
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", "attachment; filename=berita_search_engine.csv")
            self.end_headers()
            self.wfile.write(data)

        elif url.path == "/api/download/json":
            with CRAWLER_LOCK:
                articles = list(CRAWLER_STATE["articles"])

            data = json.dumps(articles, indent=4, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Disposition", "attachment; filename=berita_search_engine.json")
            self.end_headers()
            self.wfile.write(data)

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)

        if url.path == "/api/start":
            content_len = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_len)
            params = json.loads(post_data.decode("utf-8"))

            keyword = params.get("keyword", "ijazah jokowi")
            limit = int(params.get("limit", 20))
            headless = bool(params.get("headless", False))

            with CRAWLER_LOCK:
                if CRAWLER_STATE["is_running"]:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Spider sedang berjalan"}).encode("utf-8"))
                    return

            t = threading.Thread(
                target=crawler_worker,
                args=(keyword, limit, headless),
                daemon=True
            )
            t.start()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "started"}).encode("utf-8"))

        elif url.path == "/api/stop":
            with CRAWLER_LOCK:
                CRAWLER_STATE["should_stop"] = True

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "stopped"}).encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()


def run_server(port=5000):
    server_address = ("127.0.0.1", port)
    httpd = ThreadingHTTPServer(server_address, SpiderRequestHandler)
    url = f"http://localhost:{port}"

    print("=" * 65)
    print("⚡ RESPONSIVE NEON SPIDER CRAWLER MATRIX RUNNING")
    print(f"👉 Akses Neon Cockpit di browser: {url}")
    print("=" * 65)
    print("[*] Tekan Ctrl+C di terminal jika ingin menghentikan server.")

    try:
        webbrowser.open(url)
    except Exception:
        pass

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Server dimatikan.")
        httpd.server_close()


if __name__ == "__main__":
    run_server()
