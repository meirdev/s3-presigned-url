import argparse
import os

import httpx
from tqdm.auto import tqdm
from tqdm.utils import CallbackIOWrapper

URL = ""


def generate_presigned_url(action: str, key: str):
    resp = httpx.post(URL, json={"action": action, "key": key})
    resp.raise_for_status()

    return resp.json()


def upload(filename: str) -> None:
    url = generate_presigned_url("upload", os.path.basename(filename))

    with open(filename, "rb") as fp:
        file_size = os.path.getsize(filename)

        with tqdm(
            desc="Uploading",
            total=file_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
        ) as t:
            reader_wrapper = CallbackIOWrapper(t.update, fp, "read")

            response = httpx.post(
                url["url"],
                data=url["fields"],
                files={"file": reader_wrapper},
            )
            response.raise_for_status()

        print(f"Your key is: {url['fields']['key']}")


def download(key: str, overwrite: bool) -> None:
    url = generate_presigned_url("download", key)

    with httpx.stream("GET", url) as response:
        response.raise_for_status()

        filename = response.headers["x-amz-meta-filename"]
        if not overwrite and os.path.exists(filename):
            raise FileExistsError(f"File {filename} already exists")

        with open(filename, "wb") as fp:
            file_size = int(response.headers["Content-Length"])

            with tqdm(
                desc="Downloading",
                total=file_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            ) as t:
                for chunk in response.iter_bytes():
                    fp.write(chunk)
                    t.update(len(chunk))

        print(f"File saved as {filename}")


def main() -> None:
    parser = argparse.ArgumentParser("Upload and download files")

    action_parser = parser.add_subparsers(dest="action", required=True)

    upload_parser = action_parser.add_parser("upload")
    upload_parser.add_argument("filename")

    download_parser = action_parser.add_parser("download")
    download_parser.add_argument("key")
    download_parser.add_argument(
        "-w", "--overwrite", action="store_true", help="Overwrite existing files"
    )

    args = parser.parse_args()

    if args.action == "upload":
        upload(args.filename)
    elif args.action == "download":
        download(args.key, args.overwrite)
    else:
        raise ValueError(f"Invalid action: {args.action}")


if __name__ == "__main__":
    main()
