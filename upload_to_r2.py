"""
upload_to_r2.py
---------------
Uploads the generated dua carousel slides to a Cloudflare R2 bucket
using boto3 (S3-compatible API).

Required environment variables:
    R2_ACCOUNT_ID        - Cloudflare account ID
    R2_ACCESS_KEY_ID     - R2 access key
    R2_SECRET_ACCESS_KEY - R2 secret key
    R2_BUCKET_NAME       - Bucket name
    R2_PUBLIC_URL        - Public base URL for the bucket
                           e.g. "https://pub-xxxx.r2.dev"
"""

import os
import boto3
from pathlib import Path
from botocore.config import Config


# ── Client ───────────────────────────────────────────────────────────────────
def _get_r2_client():
    account_id = os.environ["R2_ACCOUNT_ID"]
    access_key = os.environ["R2_ACCESS_KEY_ID"]
    secret_key = os.environ["R2_SECRET_ACCESS_KEY"]
    endpoint   = f"https://{account_id}.r2.cloudflarestorage.com"

    return boto3.client(
        "s3",
        endpoint_url          = endpoint,
        aws_access_key_id     = access_key,
        aws_secret_access_key = secret_key,
        config                = Config(signature_version="s3v4"),
        region_name           = "auto",
    )


# ── Upload ───────────────────────────────────────────────────────────────────
def upload_images(image_paths: dict) -> dict:
    """
    Uploads all carousel slides in image_paths to R2.

    image_paths keys expected:
        slide_1, slide_2, slide_3

    Returns same keys mapped to their full public URLs, e.g.:
        {
            "slide_1": "https://pub-xxxx.r2.dev/duas/dua_003_..._slide1.jpg",
            "slide_2": "https://pub-xxxx.r2.dev/duas/dua_003_..._slide2.jpg",
            "slide_3": "https://pub-xxxx.r2.dev/duas/dua_003_..._slide3.jpg",
        }
    """
    bucket     = os.environ["R2_BUCKET_NAME"]
    public_url = os.environ["R2_PUBLIC_URL"].rstrip("/")
    client     = _get_r2_client()
    urls       = {}

    for label, file_path in image_paths.items():
        path = Path(file_path)
        if not path.exists():
            print(f"  ⚠  Skipping {label}: file not found at {file_path}")
            continue

        object_key = f"duas/{path.name}"

        print(f"  Uploading {label} → r2://{bucket}/{object_key} ...")
        client.upload_file(
            Filename    = str(path),
            Bucket      = bucket,
            Key         = object_key,
            ExtraArgs   = {"ContentType": "image/jpeg"},
        )

        urls[label] = f"{public_url}/{object_key}"
        print(f"  ✓ {label}: {urls[label]}")

    return urls


# ── Entry point (for testing standalone) ─────────────────────────────────────
if __name__ == "__main__":
    from generate_image import generate

    result = generate()
    image_paths = {
        "slide_1": result["slide_1"],
        "slide_2": result["slide_2"],
        "slide_3": result["slide_3"],
    }

    urls = upload_images(image_paths)
    print("\nUploaded URLs:")
    for k, v in urls.items():
        print(f"  {k}: {v}")
