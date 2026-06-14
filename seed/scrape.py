#!/usr/bin/env python3
"""
scrape.py — Scrapes Mr. Sushi menu from mrsushi.pe (Justo platform, SSR HTML).

All product data is embedded in window.__remixContext on /pedir — no per-product
requests needed. Images are downloaded separately.

Run from project root:
    source backend/.venv/bin/activate
    python backend/seed/scrape.py
"""

import json
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.mrsushi.pe"
LISTING_URL = f"{BASE_URL}/pedir"
SEED_DIR = Path(__file__).parent
IMAGES_DIR = SEED_DIR / "images"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-PE,es;q=0.9,en;q=0.8",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_remix_context(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script"):
        if script.string and "__remixContext" in script.string:
            m = re.search(
                r"window\.__remixContext\s*=\s*(\{.*\})", script.string, re.DOTALL
            )
            if m:
                return json.loads(m.group(1))
    return {}


def scrape_category_map(soup: BeautifulSoup) -> dict:
    """
    Parses the listing page HTML.
    Returns {product_path: category_name} using first occurrence
    (a product can appear in Promociones AND its original category; we keep the
    first heading it appears under).
    """
    path_to_category: dict[str, str] = {}
    for container in soup.find_all("div", class_="categoryContainer"):
        h3 = container.find("h3")
        if not h3:
            continue
        category = h3.get_text(strip=True)
        for a in container.find_all(
            "a",
            href=lambda h: h and "/pedir/" in h and h.count("/") >= 3,
        ):
            path = a["href"]
            if path not in path_to_category:
                path_to_category[path] = category
    return path_to_category


def get_image_url(product: dict) -> str | None:
    images = product.get("images", [])
    if not images:
        return None
    resized = images[0].get("resizedData", {})
    # Prefer medium (800px), fall back to large or small
    return (
        resized.get("mediumURL")
        or resized.get("largeURL")
        or resized.get("smallURL")
    )


def download_image(img_url: str, product_id: str) -> str | None:
    ext = Path(urlparse(img_url).path).suffix or ".webp"
    local_path = IMAGES_DIR / f"{product_id}{ext}"
    if local_path.exists():
        return str(local_path.relative_to(SEED_DIR.parent.parent))  # relative to repo
    try:
        r = requests.get(img_url, headers={"Referer": BASE_URL}, timeout=20)
        r.raise_for_status()
        local_path.write_bytes(r.content)
        return str(local_path.relative_to(SEED_DIR.parent.parent))
    except Exception as e:
        print(f"    [WARN] image download failed ({product_id}): {e}")
        return None


def map_modifier(mod: dict) -> dict:
    """
    Maps a Justo modifier group to our option schema.

    Justo field semantics:
      mod.min  = minimum selections required from this group
      mod.max  = 0 → no upper limit on the group; N → exactly up to N
                 (When max=0 and min=1, the UI renders radio buttons — "choose 1".)
      option.max = per-option quantity cap (0 = unlimited)

    Our mapping:
      max=0 or max=1  → radio  (min=1, max=1)
      max==min, options_count==max, max>1 → quantity  (distribute N units among N choices)
      otherwise (max>1)                  → checkbox  (min=mod.min, max=mod.max)
    """
    name = mod["name"]
    choices = [opt["name"] for opt in mod.get("options", [])]
    min_v: int = mod.get("min") or 1
    max_v = mod.get("max")  # None or 0 means no group-level cap

    if max_v is None or max_v == 0 or max_v == 1:
        return {"name": name, "type": "radio", "min": 1, "max": 1, "choices": choices}

    options_count = len(choices)
    if min_v == max_v == options_count:
        # "Distribute exactly N units among exactly N choices" — quantity counter.
        # Confirmed for: Box Especial (5/5), Piqueo Express (3/3).
        return {"name": name, "type": "quantity", "total": max_v, "choices": choices}

    return {"name": name, "type": "checkbox", "min": min_v, "max": max_v, "choices": choices}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    print(f"GET {LISTING_URL} ...")
    r = requests.get(LISTING_URL, headers=HEADERS, timeout=20)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    # 1. Extract category assignments from rendered HTML sections
    path_to_category = scrape_category_map(soup)
    print(f"  HTML category map: {len(path_to_category)} unique product paths")

    # 2. Extract all product data from embedded Remix JSON context
    ctx = extract_remix_context(r.text)
    layout_data = (
        ctx.get("state", {})
        .get("loaderData", {})
        .get("pages/Order/Layout/index", {})
    )
    products_json: dict = layout_data.get("menuData", {}).get("products", {})
    print(f"  Remix context: {len(products_json)} products")

    path_to_product = {p["path"]: p for p in products_json.values() if p.get("path")}

    # 3. Build catalog
    catalog = []
    failed = []

    for path, category in path_to_category.items():
        product = path_to_product.get(path)
        if not product:
            print(f"  [WARN] No JSON data for path: {path}")
            failed.append({"path": path, "reason": "missing from JSON context"})
            continue

        # productId = last URL segment  (/pedir/<id>/<slug> → <slug>)
        product_id = path.rstrip("/").split("/")[-1]

        # Price: finalPrice reflects active discounts (what customers pay)
        avail = product.get("availabilityAt", {})
        price = float(avail.get("finalPrice") or avail.get("basePrice") or 0.0)

        # Image
        img_url = get_image_url(product)
        image_file = ""
        if img_url:
            image_file = download_image(img_url, product_id) or ""
            time.sleep(0.4)

        # Options
        options = []
        for mod in product.get("modifiers", []):
            if mod.get("options"):
                options.append(map_modifier(mod))

        catalog.append(
            {
                "productId": product_id,
                "name": product.get("name", ""),
                "description": (product.get("description") or "").strip(),
                "price": round(price, 2),
                "category": category,
                "imageFile": image_file,
                "options": options,
            }
        )

    # 4. Write catalog.json
    catalog_path = SEED_DIR / "catalog.json"
    catalog_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False))

    # 5. Report
    with_opts = [p for p in catalog if p["options"]]
    without_opts = [p for p in catalog if not p["options"]]
    quantity_entries = [
        (p["name"], o)
        for p in catalog
        for o in p["options"]
        if o["type"] == "quantity"
    ]

    print(f"\n=== DONE ===")
    print(f"catalog.json: {len(catalog)} products")
    print(f"  with options populated : {len(with_opts)}")
    print(f"  with options=[]        : {len(without_opts)}")

    if failed:
        print(f"\nFailed ({len(failed)}):")
        for f in failed:
            print(f"  {f['path']} — {f['reason']}")

    if quantity_entries:
        print(f"\nQuantity-type modifier groups ({len(quantity_entries)}):")
        for pname, opt in quantity_entries:
            print(
                f"  [{pname}] '{opt['name']}' "
                f"total={opt['total']}, choices={len(opt['choices'])}"
            )

    # Show a few products with options for quick sanity-check
    print("\nSample products with options:")
    for p in with_opts[:3]:
        print(f"  {p['name']}")
        for o in p["options"]:
            if o["type"] == "quantity":
                print(f"    - {o['name']} [{o['type']} total={o['total']}] {len(o['choices'])} choices")
            else:
                print(f"    - {o['name']} [{o['type']} {o['min']}-{o['max']}] {len(o['choices'])} choices")


if __name__ == "__main__":
    main()
