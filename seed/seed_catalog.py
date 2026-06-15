"""
Sube el catálogo de Mr. Sushi a DynamoDB + S3.

Lee seed/catalog.json (generado por seed/scrape.py) y para cada producto:
  - Sube la imagen a S3 bajo products/<productId>.<ext> (ACL: public-read)
  - Escribe el item en ProductsTable con batch_writer

Corre desde la raíz de backend/:
    python -m seed.seed_catalog

Requiere credenciales AWS activas (~/.aws/credentials).
"""

import json
import os
import sys
from decimal import Decimal
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.kitchen_stations import CATEGORY_TO_STATION

REGION = "us-east-1"
STAGE = sys.argv[1] if len(sys.argv) > 1 else "dev"
PRODUCTS_TABLE = f"mrsushi-products-{STAGE}"
MENU_BUCKET = f"mrsushi-menu-images-{STAGE}"

SEED_DIR = Path(__file__).parent
CATALOG_PATH = SEED_DIR / "catalog.json"

# ---------------------------------------------------------------------------
# AWS clients
# ---------------------------------------------------------------------------

dynamo = boto3.resource("dynamodb", region_name=REGION)
table = dynamo.Table(PRODUCTS_TABLE)

s3 = boto3.client("s3", region_name=REGION)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def to_decimal(obj):
    """Recursively convert floats to Decimal (boto3 resource API requirement)."""
    return json.loads(json.dumps(obj), parse_float=Decimal)


def upload_image(local_path: str, product_id: str) -> str | None:
    """Uploads image to S3. Returns the public URL or None on failure."""
    p = Path(local_path)
    if not p.exists():
        # Try resolving relative to repo root (scrape.py stores relative paths)
        p = Path(__file__).parent.parent.parent / local_path
    if not p.exists():
        return None

    key = f"products/{p.name}"
    try:
        s3.upload_file(
            str(p),
            MENU_BUCKET,
            key,
            ExtraArgs={"ACL": "public-read", "ContentType": _content_type(p.suffix)},
        )
        return f"https://{MENU_BUCKET}.s3.{REGION}.amazonaws.com/{key}"
    except ClientError as e:
        print(f"    [WARN] S3 upload failed ({p.name}): {e}")
        return None


def _content_type(ext: str) -> str:
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }.get(ext.lower(), "application/octet-stream")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    catalog = json.loads(CATALOG_PATH.read_text())
    print(f"\nSeeding {len(catalog)} products → {PRODUCTS_TABLE} / s3://{MENU_BUCKET}")
    print("─" * 60)

    written = 0
    img_ok = 0
    img_fail = 0

    with table.batch_writer() as batch:
        for product in catalog:
            product_id = product["productId"]
            category = product["category"]

            # Upload image
            image_url = ""
            if product.get("imageFile"):
                url = upload_image(product["imageFile"], product_id)
                if url:
                    image_url = url
                    img_ok += 1
                    print(f"  img OK   {product_id}")
                else:
                    img_fail += 1
                    print(f"  img FAIL {product_id}")
            else:
                img_fail += 1

            kitchen_station = CATEGORY_TO_STATION.get(category)

            item = to_decimal({
                "PK": "BRAND#mrsushi",
                "SK": f"CAT#{category}#PROD#{product_id}",
                "GSI1PK": f"PROD#{product_id}",
                "productId": product_id,
                "name": product["name"],
                "description": product["description"],
                "price": product["price"],
                "category": category,
                "imageUrl": image_url,
                "options": product["options"],
                "kitchenStation": kitchen_station,
            })

            batch.put_item(Item=item)
            written += 1

    print(f"\n{'─' * 60}")
    print(f"Products written : {written}")
    print(f"Images uploaded  : {img_ok} OK / {img_fail} failed")
    print()


if __name__ == "__main__":
    main()
