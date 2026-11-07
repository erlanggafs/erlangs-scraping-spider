import argparse
import base64
import csv
import json
import urllib.parse
from scrapling.fetchers import StealthyFetcher


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


def scrape_search_engine(keyword: str, limit: int = 20, max_pages: int = 5, headless: bool = False):
    """
    Mencari berita secara bebas dari seluruh domain di internet menggunakan Search Engine.
    Tidak dibatasi ke satu atau dua portal saja (menangkap Kompas, Detik, Tempo, Liputan6, CNN, dll).
    """
    encoded_query = urllib.parse.quote_plus(keyword)
    all_articles = []
    seen_urls = set()

    print("=" * 65)
    print("[*] MEMULAI SCRAPING SEARCH ENGINE (BEBAS SEMUA DOMAIN)")
    print(f"[*] Kata Kunci   : '{keyword}'")
    print(f"[*] Target Batas : {limit} artikel")
    print(f"[*] Mode Browser : {'Headless (Latar Belakang)' if headless else 'GUI / Muncul di Layar'}")
    print("=" * 65)

    for page_idx in range(max_pages):
        # Pagination Bing News: &first=1, &first=11, &first=21, ...
        offset = (page_idx * 10) + 1
        target_url = f"https://www.bing.com/news/search?q={encoded_query}&first={offset}"
        print(f"\n[+] [Search Engine] Membuka halaman {page_idx + 1} (Offset {offset}): {target_url}")

        try:
            response = StealthyFetcher.fetch(
                target_url,
                headless=headless,
                network_idle=True,
                timeout=30000
            )

            if response.status != 200:
                print(f"[!] Search Engine mengembalikan status {response.status}. Melewati...")
                continue

            cards = response.css(".news-card")
            print(f"    Ditemukan {len(cards)} artikel di halaman ini.")

            if not cards:
                print("[*] Tidak ada lagi hasil di mesin pencari. Selesai.")
                break

            for c in cards:
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

                all_articles.append({
                    "sumber": author,
                    "domain": domain,
                    "judul": title,
                    "waktu": time_val,
                    "ringkasan": snippet,
                    "url": clean_url
                })

                if len(all_articles) >= limit:
                    print(f"\n[✓] Batas target {limit} berita berhasil tercapai!")
                    break

            if len(all_articles) >= limit:
                break

        except Exception as e:
            print(f"[!] Terjadi kesalahan saat memproses halaman {page_idx + 1}: {e}")

    return all_articles[:limit]


def save_results(articles, file_prefix="berita_search_engine"):
    if not articles:
        print("\n[!] Tidak ada data berita yang berhasil diambil.")
        return

    # 1. Simpan ke JSON
    json_path = f"{file_prefix}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=4, ensure_ascii=False)
    print(f"\n[v] Berhasil menyimpan {len(articles)} berita ke: {json_path}")

    # 2. Simpan ke CSV
    csv_path = f"{file_prefix}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["sumber", "domain", "judul", "waktu", "ringkasan", "url"])
        writer.writeheader()
        writer.writerows(articles)
    print(f"[v] Berhasil menyimpan file CSV ke: {csv_path}")


def main():
    parser = argparse.ArgumentParser(description="Scraping berita bebas domain via Search Engine menggunakan Scrapling.")
    parser.add_argument("--keyword", "-k", default="ijazah jokowi", help="Kata kunci pencarian berita (default: 'ijazah jokowi')")
    parser.add_argument("--limit", "-l", type=int, default=20, help="Batas maksimal total berita (default: 20)")
    parser.add_argument("--max-pages", "-p", type=int, default=5, help="Batas maksimal halaman search engine (default: 5)")
    parser.add_argument("--headless", action="store_true", default=False, help="Jalankan browser di background tanpa tampilan GUI")
    parser.add_argument("--output", "-o", default="hasil", help="Nama prefix file output (default: 'hasil')")
    
    args = parser.parse_args()

    results = scrape_search_engine(
        keyword=args.keyword,
        limit=args.limit,
        max_pages=args.max_pages,
        headless=args.headless
    )

    # Tampilkan preview hasil di terminal
    print("\n" + "=" * 65)
    print(f"PREVIEW HASIL ({len(results)} Berita Ditemukan dari Berbagai Domain Bebas):")
    print("=" * 65)
    for i, item in enumerate(results[:8], start=1):
        print(f"\n[{i}] [{item['sumber']} | {item['domain']}] {item['judul']}")
        print(f"    Waktu    : {item['waktu']}")
        print(f"    Ringkasan: {item['ringkasan'][:90]}..." if len(item['ringkasan']) > 90 else f"    Ringkasan: {item['ringkasan']}")
        print(f"    Link     : {item['url']}")

    if len(results) > 8:
        print(f"\n... dan {len(results) - 8} berita lainnya.")

    save_results(results, file_prefix=args.output)


if __name__ == "__main__":
    main()
