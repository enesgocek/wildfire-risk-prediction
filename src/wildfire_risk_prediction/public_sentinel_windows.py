"""Bounded public Sentinel-2 reads. Temporary access tokens never leave memory."""

import hashlib
from urllib.parse import urlsplit

import numpy as np
import rasterio
import requests
from affine import Affine

from wildfire_risk_prediction.imagery_review import bounded_window, support_quality


def public_asset(href):
    u = urlsplit(href)
    if (
        u.scheme != "https"
        or u.netloc
        not in (
            "sentinel2l2a01.blob.core.windows.net",
            "sentinel2l2a02.blob.core.windows.net",
        )
        or u.query
        or u.fragment
        or not u.path.startswith("/sentinel2-l2/")
    ):
        raise ValueError("Unexpected public asset")
    return u.hostname.split(".")[0], "sentinel2-l2"


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


class PublicWindows:
    def __init__(self):
        self.session = requests.Session()
        self.session.trust_env = False
        self.tokens = {}

    def close(self):
        self.tokens.clear()
        self.session.close()

    def sign(self, href):
        account, container = public_asset(href)
        key = account, container
        if key not in self.tokens:
            response = self.session.get(
                f"https://planetarycomputer.microsoft.com/api/sas/v1/token/{account}/{container}",
                timeout=(15, 30),
                allow_redirects=False,
            )
            require(response.status_code == 200, "Public token unavailable")
            self.tokens[key] = response.json()["token"]
        return href + "?" + self.tokens[key]

    def head(self, url):
        response = self.session.head(url, timeout=(15, 30), allow_redirects=False)
        require(response.status_code == 200 and response.headers.get("ETag"), "Asset headers")
        return {k: response.headers.get(k) for k in ("ETag", "Last-Modified", "Content-Length")}

    def read(self, item, polygon, folder):
        """Read native TCI/SCL crops, verify unchanged source and lossless local roundtrip."""
        epsg = item["properties"]["proj:epsg"]
        require(epsg in (32635, 32636), "Expected local UTM")
        assets, quality = {}, None
        for band, count, resolution in (("SCL", 1, 20), ("visual", 3, 10)):
            asset = item["assets"][band]
            signed = self.sign(asset["href"])
            before = self.head(signed)
            with rasterio.Env(
                GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
                GDAL_PAM_ENABLED="NO",
                GDAL_HTTP_TIMEOUT="30",
                GDAL_HTTP_CONNECTTIMEOUT="15",
                GDAL_HTTP_MAX_RETRY="0",
                CPL_DEBUG=False,
                CPL_CURL_VERBOSE=False,
                CPL_LOG="NUL",
                GDAL_TIFF_INTERNAL_MASK=True,
            ):
                with rasterio.open(signed) as src:
                    require(src.crs.to_epsg() == epsg and src.count == count, "Raster identity")
                    require(src.transform == Affine(*asset["proj:transform"]), "Transform")
                    require(
                        src.res == (resolution, resolution) and src.dtypes == ("uint8",) * count,
                        "Native encoding",
                    )
                    window = bounded_window(
                        polygon.bounds, src.transform, src.width, src.height, clip_context=True
                    )
                    array = src.read(window=window)
                    valid = src.dataset_mask(window=window) > 0
                    affine = src.window_transform(window)
                require(before == self.head(signed), "Source changed during read")
                destination = folder / f"{band}.tif"
                with rasterio.open(
                    destination,
                    "w",
                    driver="GTiff",
                    width=array.shape[2],
                    height=array.shape[1],
                    count=count,
                    dtype="uint8",
                    crs=epsg,
                    transform=affine,
                    compress="deflate",
                ) as dst:
                    dst.write(array)
                    dst.write_mask(valid.astype("uint8") * 255)
                with rasterio.open(destination) as check:
                    require(
                        np.array_equal(check.read(), array)
                        and np.array_equal(check.dataset_mask() > 0, valid)
                        and check.transform == affine
                        and check.crs.to_epsg() == epsg,
                        "Crop roundtrip",
                    )
                if band == "SCL":
                    quality = support_quality(array[0], valid, affine, polygon)
            assets[band] = {
                "unsigned_href": asset["href"],
                "headers": before,
                "window": list(window.flatten()),
                "shape": list(array.shape),
                "transform": list(affine)[:6],
                "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
            }
            del signed
        return assets, quality
