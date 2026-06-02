import hashlib
import json
import random
import time
from copy import deepcopy
import os
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse
import ddddocr
UI_WIDTH = 340
DEFAULT_FONT_HASH = "1ba6eed9691ac266961608109d3e9807382e43853b43ad797cb8ab46"
ZERO_WIDTH_JOINER = "\u200d"
DEFAULT_ZWJ_COUNT = 1
OBSERVED_D_DELTAS = (2, 5, 6, 7, 8, 9, 11, 12)
OBSERVED_F_VALUES = (9, 11, 13, 5, 1, 12, 2, 0, 7, 4, 6)
OBSERVED_FPS_VALUES = (62, 63, 61)
OBSERVED_G_VALUES = (1, 5, 17, 12, 7, 13, 0, 3, 8, 2, 4, 14, 15)
OBSERVED_MASK_SUFFIXES_759 = (13, 14, 16, 18, 21, 22, 26, 28, 30, 33, 34, 35, 37, 40, 41, 43, 45, 46, 49, 51, 53, 55, 57)
OBSERVED_ENV_FINGERPRINTS_759 = (
    ((1, 1, 3), (4, 2, 3), ("5", "b"), (2, 63, 4)),
    ((3, 5, 49), (3, 4, 1), ("6", "1"), (7, 63, 11)),
    ((3, 1, 9), (4, 2, 2), ("9", "6"), (6, 61, 2)),
    ((3, 2, 13), (4, 3, 2), ("8", "5"), (6, 63, 4)),
    ((3, 3, 29), (3, 3, 1), ("6", "3"), (5, 63, 15)),
    ((1, 4, 41), (3, 2, 2), ("6", "f"), (9, 62, 1)),
    ((0, 2, 4), (3, 2, 2), ("4", "4"), (0, 63, 8)),
    ((1, 3, 13), (1, 1, 0), ("1", "0"), (11, 61, 17)),
    ((2, 3, 18), (0, 4, 2), ("1", "5"), (13, 63, 5)),
    ((1, 2, 10), (4, 3, 4), ("4", "8"), (1, 63, 7)),
    ((1, 2, 7), (3, 0, 4), ("", "3"), (1, 63, 7)),
    ((1, 2, 19), (3, 2, 3), ("1", "4"), (7, 63, 5)),
    ((2, 4, 28), (3, 4, 0), ("4", "2"), (9, 62, 13)),
    ((0, 5, 12), (4, 3, 0), ("6", "d"), (12, 63, 0)),
    ((2, 3, 23), (0, 0, 2), ("7", "5"), (1, 63, 1)),
    ((5, 2, 33), (2, 3, 0), ("9", "2"), (1, 63, 5)),
    ((2, 1, 7), (3, 2, 1), ("1", "d"), (12, 63, 8)),
    ((4, 4, 42), (4, 3, 1), ("9", "f"), (5, 62, 17)),
    ((1, 0, 3), (1, 1, 3), ("0", "5"), (1, 61, 5)),
    ((4, 2, 16), (4, 0, 2), ("6", "e"), (2, 61, 14)),
    ((3, 1, 13), (1, 4, 0), ("4", "d"), (0, 63, 0)),
    ((3, 4, 35), (3, 1, 4), ("4", "e"), (2, 63, 2)),
    ((3, 1, 5), (3, 1, 2), ("4", "a"), (4, 63, 14)),
    ((5, 3, 49), (2, 2, 4), ("4", "5"), (12, 62, 8)),
    ((2, 2, 10), (3, 1, 3), ("4", "e"), (1, 63, 15)),
    ((4, 0, 10), (4, 1, 1), ("6", "2"), (1, 63, 15)),
    ((5, 3, 25), (3, 0, 3), ("7", "6"), (5, 62, 1)),
    ((3, 2, 13), (3, 3, 4), ("0", "3"), (6, 63, 4)),
    ((2, 0, 8), (2, 3, 3), ("8", "4"), (7, 62, 15)),
    ((3, 0, 11), (0, 1, 0), ("3", "6"), (5, 63, 15)),
    ((7, 1, 33), (0, 3, 2), ("3", "8"), (12, 63, 2)),
    ((1, 3, 17), (1, 3, 4), ("1", "8"), (7, 63, 3)),
    ((6, 3, 20), (2, 1, 1), ("2", "4"), (0, 63, 0)),
    ((4, 4, 34), (2, 2, 0), ("7", "5"), (3, 63, 13)),
    ((1, 1, 3), (2, 0, 2), ("0", "3"), (11, 63, 1)),
    ((3, 2, 13), (3, 2, 3), ("1", "8"), (1, 63, 7)),
    ((2, 0, 6), (3, 2, 3), ("1", "4"), (10, 63, 12)),
    ((1, 3, 17), (3, 2, 3), ("1", "f"), (9, 63, 15)),
    ((2, 4, 28), (2, 4, 2), ("0", "d"), (5, 63, 7)),
    ((5, 1, 43), (3, 1, 4), ("4", "b"), (5, 62, 7)),
)



def _bucket_tuple(row):
    return tuple(row[0]), tuple(row[1]), tuple(row[2]), tuple(row[3])


OBSERVED_ENV_PAIR_BUCKETS_759 = {}
for _idx, _row in enumerate(OBSERVED_ENV_FINGERPRINTS_759):
    _c3, _k3, _m_pair, _runtime3 = _row
    OBSERVED_ENV_PAIR_BUCKETS_759.setdefault((_c3[0], _c3[1]), []).append(_idx)

FRESH_ENV_PAIR_PREFERRED_759 = {
    # Prefer fresh 2026-05-08 final-encrypt browser buckets over older replay
    # buckets when an exact (c0,c1) pair has been observed again.
    (4, 4): ((4, 4, 34), (2, 2, 0)),
    (1, 1): ((1, 1, 3), (4, 2, 3)),
    (1, 2): ((1, 2, 7), (3, 0, 4)),
    (3, 2): ((3, 2, 13), (3, 2, 3)),
    (2, 0): ((2, 0, 6), (3, 2, 3)),
    (1, 3): ((1, 3, 17), (3, 2, 3)),
    (2, 4): ((2, 4, 28), (2, 4, 2)),
    (5, 1): ((5, 1, 43), (3, 1, 4)),
    # Fresh browser-native success buckets captured 2026-05-11.
    (3, 1): ((3, 1, 9), (4, 2, 2)),
    (3, 3): ((3, 3, 29), (3, 3, 1)),
    (3, 5): ((3, 5, 49), (3, 4, 1)),
}

PROTOCOL_SUCCESS_BUCKET_INDEXES_759 = (0, 27, 4, 29)



def _select_observed_env_bucket_index(digest, c0, c1, captcha_id=""):
    indexed_rows = list(enumerate(OBSERVED_ENV_FINGERPRINTS_759))
    policy = os.getenv("CAPTCHA_ENV_BUCKET_POLICY", "live_pair").lower()
    success_indexes = [idx for idx in PROTOCOL_SUCCESS_BUCKET_INDEXES_759 if 0 <= idx < len(OBSERVED_ENV_FINGERPRINTS_759)]
    if policy in {"protocol_success", "pure_success", "success"} and success_indexes:
        # Pure protocol does not reproduce every live-browser env bucket with
        # equal reliability.  Prefer c2/k/runtime buckets that have produced
        # protocol 200s, while build_env_arrays() still recomputes c0/c1/m1
        # from the current challenge id.
        return success_indexes[digest[0] % len(success_indexes)]

    pair_indexes = OBSERVED_ENV_PAIR_BUCKETS_759.get((c0, c1)) or []
    if pair_indexes:
        # Same (c0,c1) rows are the only fully observed joint distributions.
        preferred = FRESH_ENV_PAIR_PREFERRED_759.get((c0, c1))
        if preferred:
            preferred_c3, preferred_k = preferred
            for idx in reversed(pair_indexes):
                row_c3, row_k, _row_m, _row_runtime = OBSERVED_ENV_FINGERPRINTS_759[idx]
                if tuple(row_c3) == tuple(preferred_c3) and tuple(row_k) == tuple(preferred_k):
                    return idx
        # Use id-tail entropy rather than detail/log_id so a known challenge id
        # keeps the same bucket across fresh detail captures.
        id_digest = hashlib.sha256(str(captcha_id)[2:].encode("utf-8")).digest()
        return pair_indexes[id_digest[0] % len(pair_indexes)]

    # Unknown pairs were noisy with nearest-neighbour sampling: several
    # plausible live buckets still returned the generic 5009 in pure protocol.
    # Prefer buckets that have produced pure-protocol 200s, while recomputing
    # c0/c1/m1 from the current challenge id in build_env_arrays().
    success_indexes = [idx for idx in PROTOCOL_SUCCESS_BUCKET_INDEXES_759 if 0 <= idx < len(OBSERVED_ENV_FINGERPRINTS_759)]
    if success_indexes:
        return success_indexes[digest[0] % len(success_indexes)]

    # Fallback only if the curated success set is unavailable.
    scored = []
    for idx, row in indexed_rows:
        rc0, rc1, _rc2 = row[0]
        dist = abs(rc0 - c0) + abs(rc1 - c1)
        scored.append((dist, idx))
    min_dist = min(dist for dist, _idx in scored)
    nearest = [idx for dist, idx in scored if dist == min_dist]
    return nearest[digest[0] % len(nearest)]

LIVE_TRACK_KEYS = (
    "id",
    "mode",
    "c",
    "8uyk1GN",
    "1ZBkmqar4",
    "Q1FvvZeZE",
    "env",
    "a",
    "b",
)
TEMPLATE_ENV_KEYS = (
    "canvas_hash",
    "webgl_hash",
    "browser",
    "gpu",
    "scale",
    "detectors",
    "mask_time",
    "loading_time",
    "ready_time",
    "d",
    "f",
    "fps",
    "g",
    "resolution",
    "browser_size",
    "page_size",
    "captcha_origin",
    "captcha_size",
)
TEMPLATE_ENV_KEYS_MATCHED = (
    "mouse_actions",
    "c",
    "k",
    "m",
    "n",
    "o",
)
BASE64_STR = 'eyJjb2RlIjoiMTAwMDAiLCJmcm9tIjoiIiwidHlwZSI6InZlcmlmeSIsInZlcnNpb24iOiIiLCJyZWdpb24iOiJjbiIsInN1YnR5cGUiOiJzbGlkZSIsInVpX3R5cGUiOiIiLCJkZXRhaWwiOiJ3eHNNQzl5TGZ6Z3gweG5RSEtxeXRobkl4V1NCaktKSmJHVkEtb1dPQy04ZG9RRkdxd053NnhmY2l6Vkc1bjFTTWk0TklKUGxva25QcVBOa3VyUXhVQ1NzTlFPLXc5aUFYR1VSa3NEbmstSllIZUVWS1kxLW0ydlBnM3NXQ1RJM21MOXBqQkItc0M2ajBWYSpMU0VQUEROSFIzbGVDNE9naUROcjdoSkdkWnJFMDZPZXBmYkRodTBaOXFjaE9Md3ZpcWNiSVk4YmFyTi1MM3N1MypHQ1ZKU3RTS1F6YXBBR0JkREhzdGZaM1cxd2tEbGs5anQxTG56VmgyNVZNMktySmlFbTBaUExxMVVMMG5OcFRUREcxZ1VBbE0tUWNWdnRyUlJCWHJKODJveGpPZjZiaDQtUTFxZGRpWXVyQlFTWFdLcFVNUjhYR1plNUtyRjYyV1B2aG5Fb01BS05FQWxTRlNUR2RrZmhuZ1dVdVE4cnhTOHJkNEZKdnIwUm5Qb1d4UDNnanQ2N3M3R0gqelpMWDgxOGFWaXFUazlJRUEuLiIsInZlcmlmeV9ldmVudCI6IjYxMjQiLCJmcCI6InZlcmlmeV9tbXp2bGlsY185ZDhiZGQ0MF8yZTBkXzYzMTdfYmNmN181NWJlNGU1YjIyZDYiLCJzZXJ2ZXJfc2RrX2VudiI6IntcImlkY1wiOlwibGZcIixcInJlZ2lvblwiOlwiQ05cIixcInNlcnZlcl90eXBlXCI6XCJ3aGFsZVwifSIsImxvZ19pZCI6IjIwMjYwMzIxMTMxNjQ5NTNEREY5NTBDMzhGODFBMTAwMjQiLCJpc19hc3Npc3RfbW9iaWxlIjpmYWxzZSwiaXNfY29tcGxleF9zbXMiOmZhbHNlLCJpZGVudGl0eV9hY3Rpb24iOiIiLCJpZGVudGl0eV9zY2VuZSI6IiIsImxvZ2luX3N0YXR1cyI6MCwiYWlkIjowfQ=='
DEFAULT_PAGE_ENV = {
    "screen": {"w": 1920, "h": 1080},
    "browser": {"w": 1686, "h": 956},
    "page": {"w": 1686, "h": 614},
    "document": {"width": 1686},
    "product_host": "www.life-data.cn",
    "vc_version": "1.0.0.306",
    "maskTime": 1778165411620,
    "h5_check_version": "4.0.5",
}

BASE_ENV_TEMPLATE = {
    "canvas_hash": "20be8370141b74c676508259b0abddaa",
    "webgl_hash": "52497e308a4259f66bf07a8977e40d65",
    "audio_hash": 196.04347745512496,
    "time_offset": -480,
    "time_zone": "Asia/Shanghai",
    "languages": ["zh-CN"],
    "plugins": [
        "PDF Viewer",
        "Chrome PDF Viewer",
        "Chromium PDF Viewer",
        "Microsoft Edge PDF Viewer",
        "WebKit built-in PDF",
    ],
    "platform": "MacIntel",
    "max_touch_points": 0,
    "webdriver": False,
    "touch_actions": [],
    "device": {"model": "Macintosh", "vendor": "Apple"},
    "os": {"name": "Mac OS", "version": "10.15.7"},
    "browser": {"name": "Chrome", "version": "147.0.0.0", "vendor": [1, 1]},
    "engine": {"name": "Blink", "version": "147.0.0.0"},
    "gpu": {
        "vendor": "Google Inc. (Apple)",
        "renderer": "ANGLE (Apple, ANGLE Metal Renderer: Apple M4, Unspecified Version)",
    },
    "resolution": "1920,1080",
    "browser_size": "1686,956",
    "page_size": "1686,614",
    "captcha_origin": "0,0",
    "captcha_size": "380, 384",
    "detectors": {
        "RegToString": {"enabled": False, "value": 0},
        "DefineId": {"enabled": True, "value": 0},
        "DateToString": {"enabled": True, "value": 0},
        "FuncToString": {"enabled": True, "value": 0},
        "Debugger": {"enabled": False, "value": 0},
        "Performance": {"enabled": True, "value": 1},
        "DebugLib": {"enabled": True, "value": 0},
    },
    "scale": "3.2.1.5",
    "o": [4],
}
h5_check_version = os.getenv("CAPTCHA_H5_CHECK_VERSION", "4.0.5")
PAYLOAD_C = [5, 7, 9, 4, 2]
USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 "
              "Safari/537.36")
AID = os.getenv("AID", "6589")
VERIFY_DICT =   {"code":"10000","from":"","type":"verify","version":"","region":"cn","subtype":"slide","ui_type":"","detail":"E32TyTNSHseYN1Bpx4lvvlvE3Ek2cgx1HOeKXKC372FOZ57lzG82Jnb12BatxiJZ-8F-Fn3QpbZHlRuacJqpNbXwzEnFcEF*rrn4*QWxymSQJVbifgti-auwKMSxDZAjdQh5YPKMczLyC390ePHhLazn7KflFDvEEkoHs9z4-6eJEJWqdIbSKJncRdjL6v-cgJRQ3JG6oZK*YWLupjtpvajmC1PGRLuF*olF6AYjv3w41gF5O4YcboWm44sRmbnRgUYY6d2LI6XIlhtLsVaa6-nfS1PfrhjmPeDqsibiKsvgTSx1c-pSEHDAIZDKldBTjrgy1-1SIiKFHjey**kPDHDCZ1cw*edWE3-qJ*j3esvRHcM9s*GFv2gHLE*xnvOkXBwf5cgQAhZHvoERfn*thM7oYLEB5w..","verify_event":"6124","fp":"verify_mnfsxxyp_e83e16c0_018c_672f_b58c_f8fc68ee07b2","server_sdk_env":"{\"idc\":\"lf\",\"region\":\"CN\",\"server_type\":\"whale\"}","log_id":"2026040116511979D67121F49BC1FC0D50","is_assist_mobile":False,"is_complex_sms":False,"identity_action":"","identity_scene":"","login_status":0,"aid":0}

SERVER_SDK_ENV = VERIFY_DICT['server_sdk_env']

SUBTYPE_MODE = VERIFY_DICT['subtype']
DETAIL = VERIFY_DICT['detail']
LOG_ID = VERIFY_DICT['log_id']

def _safe_char(text, index, default="0"):
    if isinstance(text, str) and 0 <= index < len(text):
        return text[index]
    return default


def get_distance(target_bytes, background_bytes):
    """
    ddddocr 识别滑动距离
    """
    det = ddddocr.DdddOcr(det=False, ocr=False, show_ad=False)
    return int(det.slide_match(target_bytes, background_bytes)["target"][0] * 0.6159420289855072)


def _coerce_jsonish(value):
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        return json.loads(value)
    return value


def _safe_int(value):
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _extract_state_triplet(env_util_state):
    if not isinstance(env_util_state, dict):
        return None

    values = env_util_state.get("n")
    if isinstance(values, (list, tuple)) and len(values) >= 3:
        return [int(values[0]), int(values[1]), int(values[2])]
    return None


def _extract_state_int(env_util_state, *keys):
    if not isinstance(env_util_state, dict):
        return None

    for key in keys:
        value = _safe_int(env_util_state.get(key))
        if value is not None:
            return value
    return None


def _extract_state_actions(env_util_state):
    if not isinstance(env_util_state, dict):
        return None

    for key in ("mouse_actions", "mouseActions"):
        value = env_util_state.get(key)
        if isinstance(value, (list, tuple)):
            return [str(item) for item in value]
    return None


def _normalize_mask_time_base(value):
    value = _safe_int(value)
    if value is None:
        return None
    return value // 100 if value > 10 ** 14 else value


def _parse_page_env_from_url(page_url):
    if not isinstance(page_url, str) or not page_url:
        return None

    try:
        parsed = urlparse(page_url)
        raw_env = parse_qs(parsed.query).get("env", [None])[0]
        if not raw_env:
            return None
        page_env = _coerce_jsonish(unquote(raw_env))
        if isinstance(page_env, dict):
            return page_env
    except Exception:
        return None
    return None


def _parse_page_env_from_repo_url_file():
    """Best-effort helper for the local debugging URL recorded in 网址.txt."""
    url_file = Path(__file__).resolve().parent / "网址.txt"
    try:
        for line in url_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(("http://", "https://")):
                page_env = _parse_page_env_from_url(line)
                if isinstance(page_env, dict):
                    return page_env
    except OSError:
        return None
    return None


def extract_page_env(sample=None):
    if isinstance(sample, dict):
        for key in ("page_env", "pageEnv", "query_env", "queryEnv"):
            page_env = _coerce_jsonish(sample.get(key))
            if isinstance(page_env, dict) and _safe_int(page_env.get("maskTime")) is not None:
                return page_env

        raw_env = _coerce_jsonish(sample.get("env"))
        if (
                isinstance(raw_env, dict)
                and _safe_int(raw_env.get("maskTime")) is not None
                and any(key in raw_env for key in ("screen", "browser", "page", "vc_version"))
        ):
            return raw_env

        current_page = sample.get("currentPage")
        if isinstance(current_page, dict):
            page_env = _parse_page_env_from_url(current_page.get("url"))
            if page_env:
                return page_env

        for key in ("page_url", "pageUrl", "currentPageUrl", "url"):
            page_env = _parse_page_env_from_url(sample.get(key))
            if page_env:
                return page_env

    page_env = _coerce_jsonish(os.getenv("CAPTCHA_PAGE_ENV", ""))
    if isinstance(page_env, dict) and _safe_int(page_env.get("maskTime")) is not None:
        return page_env
    page_env = _parse_page_env_from_url(os.getenv("CAPTCHA_PAGE_URL", ""))
    if isinstance(page_env, dict):
        return page_env
    if os.getenv("CAPTCHA_USE_URL_FILE_ENV", "1") != "0":
        page_env = _parse_page_env_from_repo_url_file()
        if isinstance(page_env, dict):
            return page_env
    return deepcopy(DEFAULT_PAGE_ENV)


def _format_page_env_size(size_dict):
    if not isinstance(size_dict, dict):
        return None

    width = _safe_int(size_dict.get("w"))
    height = _safe_int(size_dict.get("h"))
    if width is None or height is None:
        return None
    return f"{width},{height}"


def apply_page_env(env, sample=None):
    if not isinstance(env, dict):
        return env

    page_env = extract_page_env(sample)
    if not isinstance(page_env, dict):
        return env

    resolution = _format_page_env_size(page_env.get("screen"))
    if resolution is not None:
        env["resolution"] = resolution

    browser_size = _format_page_env_size(page_env.get("browser"))
    if browser_size is not None:
        env["browser_size"] = browser_size

    page_size = _format_page_env_size(page_env.get("page"))
    if page_size is not None:
        env["page_size"] = page_size

    return env


def _is_live_track(candidate):
    return (
            isinstance(candidate, dict)
            and isinstance(candidate.get("id"), str)
            and isinstance(candidate.get("mode"), str)
            and isinstance(candidate.get("env"), dict)
            and any(key in candidate for key in ("8uyk1GN", "Q1FvvZeZE"))
    )


def _is_live_payload(candidate):
    return _is_live_track(candidate) and "modified_img_width" in candidate


def _extract_from_candidates(container, *keys):
    for key in keys:
        if isinstance(container, dict) and key in container:
            return _coerce_jsonish(container[key])
    return None


def extract_payload_template(sample=None, captcha_id=None):
    if sample is None:
        sample = _coerce_jsonish(os.getenv("CAPTCHA_PAYLOAD_TEMPLATE", ""))
        if sample is None:
            template_file = os.getenv("CAPTCHA_PAYLOAD_TEMPLATE_FILE", "").strip()
            if template_file:
                try:
                    with open(template_file, "r", encoding="utf-8") as fh:
                        sample = _coerce_jsonish(fh.read())
                except OSError:
                    sample = None
        if sample is None:
            candidate_paths = [Path("/tmp/dy_real_plain_sample.json")]
            for sample_dir in sorted(Path("/tmp").glob("dy_real_plain_samples*")):
                candidate_paths.extend(sorted(sample_dir.glob("sample_*.json")))
            for candidate in candidate_paths:
                try:
                    with open(candidate, "r", encoding="utf-8") as fh:
                        loaded = _coerce_jsonish(fh.read())
                except OSError:
                    continue
                if _is_live_payload(loaded):
                    if captcha_id and loaded.get("id") not in (captcha_id, None):
                        continue
                    sample = loaded
                    break
                if isinstance(loaded, dict) and _is_live_payload(loaded.get("payload")):
                    if captcha_id and loaded["payload"].get("id") not in (captcha_id, None):
                        continue
                    sample = loaded["payload"]
                    break
    else:
        sample = _coerce_jsonish(sample)
    if _is_live_payload(sample):
        return deepcopy(sample)

    if isinstance(sample, dict):
        for candidate in (
                _extract_from_candidates(sample, "payload_template", "payloadTemplate", "payload", "plain_payload",
                                         "plainPayload", "lastEncryptPayloadObj"),
                _extract_from_candidates(sample, "requestData", "dataResult", "data"),
        ):
            if _is_live_payload(candidate):
                return deepcopy(candidate)

    return None


def apply_payload_template(payload, payload_template):
    if not isinstance(payload, dict) or not isinstance(payload_template, dict):
        return payload

    same_id = payload.get("id") == payload_template.get("id")

    for key in ("modified_img_width",):
        if key in payload_template:
            payload[key] = deepcopy(payload_template[key])

    if same_id:
        for key in ("c", "a", "b"):
            if key in payload_template:
                payload[key] = deepcopy(payload_template[key])
        for key in ("8uyk1GN", "1ZBkmqar4", "Q1FvvZeZE"):
            if key in payload_template:
                payload[key] = deepcopy(payload_template[key])

    template_env = payload_template.get("env")
    if isinstance(payload.get("env"), dict) and isinstance(template_env, dict):
        for key in TEMPLATE_ENV_KEYS:
            if key in template_env:
                payload["env"][key] = deepcopy(template_env[key])
        if same_id:
            for key in TEMPLATE_ENV_KEYS_MATCHED:
                if key in template_env:
                    payload["env"][key] = deepcopy(template_env[key])

    return payload


def build_font_hash(captcha_id, branch="v759"):
    """Build the browser font fingerprint embedded in slide payload.env.

    bd_version 1.0.0.759 emits the browser font hash in a growing, stateful
    shape.  The stable suffix is ``7382e43853b43ad797cb8ab46``; the prefix is
    derived from the challenge id plus a runtime-state expansion.  Clean live
    H5 samples show 40/44/48/52-char ``captcha.getTrack()`` probes and a
    56-char final ``wasm.encrypt`` payload.  Generated protocol payloads now
    default to the final 56-char shape because verify uses that path.  The
    legacy 36-char branch is retained only for older replay experiments.

    Known 1.0.0.759 samples:
      complete live desktop id=8c1661d5e936c81617c9ed20fc5c09bdd3c739ec
      font_hash=1ba66103e907382e43853b43ad797cb8ab46  # len=36
      local replay id=2429a6d6f015dd4cbdd6cc8c6c915307a80b6e08
      font_hash=1ba6a6ed1090cd3ef107372e43853b43ad797cb8ab46  # len=44
      live wasm.encrypt sample id=51caee4d497742cec2d977e120aaa95a352cde42
      font_hash=1ba6eed9691ac266961608109d3e9807382e43853b43ad797cb8ab46  # len=56, not generalized yet
    """
    if not isinstance(captcha_id, str) or len(captcha_id) < 14:
        return DEFAULT_FONT_HASH

    if branch in {"v759", "default", "current", "new", "v759_live40", "live40"}:
        # Fresh 1.0.0.759 Web/H5 final wasm.encrypt samples from real drag
        # consistently use the 40-char shape below, e.g.:
        #   4ad42fffcc2c261a5d2b215421e280813e33fc23
        #   -> 1ba62f2f0c3ec607362e43853b43ad797cb8ab46
        #   b7bcb625fb674b2f7629e8e9a87673c66fac87cd
        #   -> 1ba6b6b60b3ebb073b2e43853b43ad797cb8ab46
        # Older polluted/runtime replay samples can still use final56 below.
        return (
                "1ba6"
                + captcha_id[4:6]
                + captcha_id[4:6]
                + "0"
                + captcha_id[9]
                + "3e"
                + captcha_id[9]
                + captcha_id[13]
                + "07"
                + "3"
                + captcha_id[13]
                + "2e"
                + "43853b43ad797cb8ab46"
        )

    if branch in {"v759_final56", "final56", "sample56"}:
        return (
                "1ba6"
                + captcha_id[4:6]
                + captcha_id[18]
                + "9691"
                + captcha_id[3]
                + captcha_id[16:18]
                + "66961608109d3e980"
                + "7382e43853b43ad797cb8ab46"
        )

    if branch in {"v759_expanded", "sample44", "expanded44"}:
        return (
                "1ba6"
                + captcha_id[4:6]
                + "ed"
                + "1"
                + captcha_id[9]
                + "9"
                + captcha_id[9]
                + "c"
                + captcha_id[13]
                + "3ef1"
                + captcha_id[9]
                + "7372e"
                + "43853b43ad797cb8ab46"
        )

    if branch in {"encrypt", "v0", "short", "legacy"}:
        return (
                "1ba6"
                + captcha_id[4:6]
                + "03e"
                + captcha_id[9]
                + "07"
                + "3"
                + captcha_id[13]
                + "2e"
                + "43853b43ad797cb8ab46"
        )

    if branch == "v1":
        return (
                "1ba6"
                + captcha_id[4:6]
                + captcha_id[4:6]
                + "0"
                + captcha_id[9]
                + "3e"
                + captcha_id[9]
                + captcha_id[13]
                + "07"
                + "3"
                + captcha_id[13]
                + "2e"
                + "43853b43ad797cb8ab46"
        )

    return (
            "1ba6"
            + captcha_id[4:6]
            + captcha_id[4:6]
            + captcha_id[4]
            + captcha_id[9]
            + captcha_id[5]
            + "0"
            + captcha_id[9]
            + captcha_id[13]
            + "3e"
            + captcha_id[9]
            + captcha_id[13]
            + "07"
            + "3"
            + captcha_id[13]
            + "2e"
            + "43853b43ad797cb8ab46"
    )


def _captcha_id_env_counts(captcha_id):
    """Derive env.c[0], env.c[1] and env.m[1] from challenge id.

    README 8.1/8.3 (older 739 notes, still matching current 759 samples):
      start = 1 + Number(id[0] === id[1])
      tail = id.slice(start)
      c0 = count('a', tail)
      c1 = count('f', tail)
      m1 = id[8]
    """
    cid = captcha_id if isinstance(captcha_id, str) else ""
    tail = cid[2:]
    return tail.count("a"), tail.count("f"), _safe_char(cid, 7)


def derive_env_c2_from_id(captcha_id):
    """Derive 1.0.0.759 env.c[2] from challenge id.

    Current 3.5.77 + bd 1.0.0.759 samples no longer use the old
    3.5.76/739 ``id[5]``/``+6`` formula.  The recovered Web rule is:

      c0/c1 = count("a"/"f", id[2:])
      pivot = id[4]
      repeat = count(pivot, id[5:])
      c2 = repeat * (c0 + c1) + c0 * c1 + 2

    This matches the fresh live/protocol 759 samples used for convergence,
    including the browser payload id=0792bb... where c2=10.
    """
    cid = captcha_id if isinstance(captcha_id, str) else ""
    c0, c1, _m1 = _captcha_id_env_counts(cid)
    pivot = _safe_char(cid, 4, "")
    repeat = cid[5:].count(pivot) if pivot else 0
    return repeat * (c0 + c1) + c0 * c1 + 2


def derive_env_k_from_detail(detail):
    """Derive 1.0.0.759 env.k from md5(detail + "2") byte mods.

    Older 3.5.76 notes used ``md5(detail + "4")`` with byte ``% 4`` and
    slice[6:9].  Fresh 3.5.77/1.0.0.759 Web samples moved to:
      reg10 = md5(detail + "2")
      byteMods = bytes(reg10).map(byte % 5)
      k = byteMods.slice(4, 7)
    """
    digest = hashlib.md5(((detail or "") + "2").encode("utf-8")).hexdigest()
    byte_mods = [int(digest[i:i + 2], 16) % 5 for i in range(0, len(digest), 2)]
    return byte_mods[4:7], digest, byte_mods


def _choose_observed_env_fingerprint(detail, log_id, captcha_id):
    """Legacy/debug-only bucket picker retained for old experiments.

    The current default build_env_arrays() no longer calls this.  It is kept so
    CAPTCHA_ENV_ARRAY_MODE=observed759 can reproduce historical comparisons.
    """
    digest = hashlib.sha256(f"{detail}|{log_id}|{captcha_id}|env759".encode("utf-8")).digest()
    c0, c1, m1 = _captcha_id_env_counts(captcha_id)
    index = _select_observed_env_bucket_index(digest, c0, c1, captcha_id)
    row = OBSERVED_ENV_FINGERPRINTS_759[index]
    observed_c3, k3, _observed_m_pair, runtime3 = row
    c2 = int(observed_c3[2])
    return [c0, c1, c2], list(k3), m1, index, digest, tuple(runtime3)


def build_env_arrays(detail, log_id, captcha_id, font_hash=None, env_util_state=None):
    font_hash = font_hash or build_font_hash(captcha_id)

    env_mode = os.getenv("CAPTCHA_ENV_ARRAY_MODE", "hybrid759").lower()
    if env_mode in {"observed759", "bucket759", "bucket", "legacy_observed"}:
        c3, k, m1, bucket_index, digest, runtime3 = _choose_observed_env_fingerprint(detail, log_id, captcha_id)
        c0, c1, c2 = c3
        if isinstance(env_util_state, dict):
            env_util_state.setdefault("env_bucket_index", bucket_index)
            env_util_state.setdefault("env_runtime_values", list(runtime3))
            env_util_state.setdefault("env_k_md5", digest.hex())
    elif env_mode in {"algorithm759", "pure759", "algo759"}:
        c0, c1, m1 = _captcha_id_env_counts(captcha_id)
        c2 = derive_env_c2_from_id(captcha_id)
        k, md5_digest, byte_mods = derive_env_k_from_detail(detail)
        if isinstance(env_util_state, dict):
            env_util_state.setdefault("env_algorithm", "algorithm759")
            env_util_state.setdefault("env_k_md5", md5_digest)
            env_util_state.setdefault("env_k_byte_mods", list(byte_mods))
    else:
        # 759 default: strict env.c/env.k/env.m/env.n are algorithm-derived.
        # Observed buckets are retained only as a side channel for f/fps/g
        # runtime defaults; c2 itself must not come from bucket enumeration.
        c0, c1, m1 = _captcha_id_env_counts(captcha_id)
        c2 = derive_env_c2_from_id(captcha_id)
        k, md5_digest, byte_mods = derive_env_k_from_detail(detail)
        _c3, _bucket_k, _bucket_m1, bucket_index, _digest, runtime3 = _choose_observed_env_fingerprint(detail, log_id, captcha_id)
        if isinstance(env_util_state, dict):
            env_util_state.setdefault("env_algorithm", "algorithm759")
            env_util_state.setdefault("env_bucket_index", bucket_index)
            env_util_state.setdefault("env_runtime_values", list(runtime3))
            env_util_state.setdefault("env_k_md5", md5_digest)
            env_util_state.setdefault("env_k_byte_mods", list(byte_mods))

    m2_base = "5" if k[2] in {0, 1, 4} else "7"
    m = [
        _safe_char(log_id, 11),
        m1,
        m2_base + ZERO_WIDTH_JOINER * DEFAULT_ZWJ_COUNT,
    ]
    c = [c0, c1, c2, 124, 10]
    n = [c2 + 12]

    if isinstance(env_util_state, dict):
        state_triplet = _extract_state_triplet(env_util_state)
        if state_triplet:
            c[:3] = state_triplet
            n = [state_triplet[2] + 12]
            env_k = env_util_state.get("k")
            if isinstance(env_k, (list, tuple)) and len(env_k) >= 3:
                k = [int(env_k[0]), int(env_k[1]), int(env_k[2])]
            env_m = env_util_state.get("m")
            if (
                    isinstance(env_m, (list, tuple))
                    and len(env_m) >= 3
                    and ZERO_WIDTH_JOINER in str(env_m[2])
            ):
                m = [str(env_m[0]), str(env_m[1]), str(env_m[2])]

    return {
        "c": c,
        "k": k,
        "m": m,
        "n": n,
    }

def _derive_m_suffix(k_values, mouse_actions=None, font_hash=None):
    if isinstance(k_values, (list, tuple)) and len(k_values) >= 3 and k_values[2] in {0, 1, 4}:
        prefix = "5"
    else:
        prefix = "7"

    # The ZWJ tail is runtime-stateful and follows the expanded font fingerprint
    # length, not a small enum bucket.  Current 1.0.0.759 browser samples:
    #   font_hash.len=40  -> 1  ZWJ (clean generated/fresh protocol state)
    #   font_hash.len=88  -> 13 ZWJ
    #   font_hash.len=100 -> 16 ZWJ
    # So the recovered rule is:
    #   zwj = max(1, floor((font_hash.length - 36) / 4))
    # mouse_actions growth is correlated browser state, but it must not cap the
    # value: updated real browser sample has mouse_actions.len=10 and 16 ZWJ.
    if isinstance(font_hash, str) and len(font_hash) > 40:
        zwj_count = max(DEFAULT_ZWJ_COUNT, (len(font_hash) - 36) // 4)
    else:
        zwj_count = DEFAULT_ZWJ_COUNT

    return prefix + ZERO_WIDTH_JOINER * int(max(DEFAULT_ZWJ_COUNT, zwj_count))


def _derive_o_values(mouse_actions=None):
    return [4]


def apply_env_util_state(env, env_util_state):
    if not isinstance(env, dict) or not isinstance(env_util_state, dict):
        return env

    state_triplet = _extract_state_triplet(env_util_state)
    if state_triplet:
        env["c"] = [state_triplet[0], state_triplet[1], state_triplet[2], 124, 10]
        env["n"] = [state_triplet[2] + 12]

        env_k = env_util_state.get("k")
        if isinstance(env_k, (list, tuple)) and len(env_k) >= 3:
            env["k"] = [int(env_k[0]), int(env_k[1]), int(env_k[2])]

        env_m = env_util_state.get("m")
        if (
                isinstance(env_m, (list, tuple))
                and len(env_m) >= 3
                and ZERO_WIDTH_JOINER in str(env_m[2])
        ):
            env["m"] = [str(env_m[0]), str(env_m[1]), str(env_m[2])]

    loading_time = _extract_state_int(env_util_state, "loadingTime", "loading_time")
    if loading_time is not None:
        env["loading_time"] = loading_time

    ready_time = _extract_state_int(env_util_state, "readyTime", "ready_time")
    if ready_time is not None:
        env["ready_time"] = ready_time

    mask_time_base = _normalize_mask_time_base(
        _extract_state_int(env_util_state, "maskTime", "mask_time")
    )
    if mask_time_base is not None and "mask_time" not in env:
        env["mask_time"] = mask_time_base * 100 + 2

    if "scale" in env_util_state:
        env["scale"] = str(env_util_state["scale"])

    if "d" not in env:
        d_value = _extract_state_int(env_util_state, "d")
        if d_value is not None:
            env["d"] = d_value

    if "f" not in env:
        f_value = _extract_state_int(env_util_state, "f")
        if f_value is not None:
            env["f"] = f_value

    if "fps" not in env:
        fps_value = _extract_state_int(env_util_state, "fps")
        if fps_value is not None:
            env["fps"] = fps_value

    if "g" not in env:
        g_value = _extract_state_int(env_util_state, "g")
        if g_value is not None:
            env["g"] = g_value

    if "mouse_actions" not in env:
        mouse_actions = _extract_state_actions(env_util_state)
        if mouse_actions is not None:
            env["mouse_actions"] = mouse_actions

    return env


def legacy_payload_to_live_track(payload):
    if not isinstance(payload, dict) or "id" not in payload or "env" not in payload:
        return None

    if _is_live_track(payload):
        track = deepcopy(payload)
        track.pop("modified_img_width", None)
        return track

    if "qiQezhn" not in payload and "cIxHF" not in payload:
        return None

    old_track = payload.get("cIxHF", {})
    return {
        "id": payload.get("id", ""),
        "mode": payload.get("mode", SUBTYPE_MODE),
        "c": deepcopy(payload.get("c", PAYLOAD_C)),
        "8uyk1GN": deepcopy(payload.get("qiQezhn", [])),
        "1ZBkmqar4": deepcopy(payload.get("vEfx2", [])),
        "Q1FvvZeZE": {
            "AGV8DioD": deepcopy(old_track.get("Dd8PDU", {})),
            "2MILE": deepcopy(old_track.get("qhKhWm", {})),
            "J9c": deepcopy(old_track.get("uye", [])),
            "FrZXd9GD": deepcopy(old_track.get("FrZXd9GD", [])),
            "rHqT9pMS": deepcopy(old_track.get("3lf8", [])),
            "pE2N": deepcopy(old_track.get("Hxh", [])),
        },
        "env": deepcopy(payload.get("env", {})),
        "a": payload.get("a"),
        "b": payload.get("b"),
    }


def extract_track_from_live_result(live_result):
    sample = _coerce_jsonish(live_result)
    if _is_live_track(sample):
        return deepcopy(sample)

    if _is_live_payload(sample):
        track = deepcopy(sample)
        track.pop("modified_img_width", None)
        return track

    if isinstance(sample, dict):
        for candidate in (
                _extract_from_candidates(sample, "track", "payload", "plain_payload", "plainPayload",
                                         "lastEncryptPayloadObj"),
                _extract_from_candidates(sample, "requestData", "dataResult", "data"),
        ):
            if _is_live_track(candidate):
                return deepcopy(candidate)
            if _is_live_payload(candidate):
                track = deepcopy(candidate)
                track.pop("modified_img_width", None)
                return track
            legacy_track = legacy_payload_to_live_track(candidate)
            if legacy_track:
                return legacy_track

    return legacy_payload_to_live_track(sample)


def extract_modified_img_width_from_live_result(live_result):
    sample = _coerce_jsonish(live_result)
    if isinstance(sample, dict):
        value = _safe_int(sample.get("modified_img_width"))
        if value is not None:
            return value

        for nested_key in ("payload", "plain_payload", "plainPayload", "lastEncryptPayloadObj", "requestData", "data"):
            nested = _coerce_jsonish(sample.get(nested_key))
            if isinstance(nested, dict):
                value = _safe_int(nested.get("modified_img_width"))
                if value is not None:
                    return value
    return None


def extract_distance_from_live_result(live_result):
    sample = _coerce_jsonish(live_result)
    if isinstance(sample, dict):
        for key in ("distance", "modified_img_width"):
            value = sample.get(key)
            if isinstance(value, (int, float)):
                return int(value)

        for nested_key in ("payload", "plain_payload", "plainPayload", "lastEncryptPayloadObj", "requestData", "data"):
            nested = _coerce_jsonish(sample.get(nested_key))
            if isinstance(nested, dict):
                value = nested.get("modified_img_width")
                if isinstance(value, (int, float)):
                    return int(value)
    return None


def _extract_detail_and_log_id(sample, detail=None, log_id=None):
    if detail and log_id:
        return detail, log_id

    if isinstance(sample, dict):
        verify_data = _extract_from_candidates(sample, "verifyData", "verify_data")
        if isinstance(verify_data, dict):
            detail = detail or verify_data.get("detail")
            log_id = log_id or verify_data.get("log_id")

    return detail, log_id


def derive_mask_time_suffix(detail, log_id, captcha_id, *, ready_time=None, runtime_state=None):
    runtime_state = runtime_state or {}
    for key in ("mask_time_suffix", "maskTimeSuffix"):
        value = _safe_int(runtime_state.get(key))
        if value is not None:
            return max(0, min(99, value))

    # 1.0.0.759 browser payloads use a challenge/runtime-looking suffix, but
    # observed values are bounded and not equal to mouse/ready timestamp tails.
    # Pick from the clean browser suffix set with a stable per-challenge digest
    # so retries for the same challenge remain reproducible.
    anchor = _safe_int(ready_time) or 0
    digest = hashlib.md5(
        f"{detail}|{log_id}|{captcha_id}|{anchor}|mask_time_suffix759".encode("utf-8")
    ).digest()
    return OBSERVED_MASK_SUFFIXES_759[digest[0] % len(OBSERVED_MASK_SUFFIXES_759)]


def resolve_mask_time_base(
        detail,
        log_id,
        captcha_id,
        *,
        env_util_state=None,
        env_overrides=None,
        loading_time=None,
):
    if isinstance(env_overrides, dict):
        for key in ("mask_time_base", "page_mask_time", "query_mask_time"):
            value = _safe_int(env_overrides.get(key))
            if value is not None:
                return value

        page_env = extract_page_env(env_overrides)
        if isinstance(page_env, dict):
            value = _safe_int(page_env.get("maskTime"))
            if value is not None:
                return value

    if isinstance(env_util_state, dict):
        value = _normalize_mask_time_base(
            _extract_state_int(env_util_state, "maskTime", "mask_time")
        )
        if value is not None:
            return value

    page_env = extract_page_env()
    if isinstance(page_env, dict):
        value = _safe_int(page_env.get("maskTime"))
        if value is not None:
            return value

    anchor = _safe_int(loading_time) or int(time.time() * 1000)
    digest = hashlib.md5(f"{detail}|{log_id}|{captcha_id}|mask_time_base".encode("utf-8")).digest()
    offset_ms = 12_000_000 + ((digest[1] << 8 | digest[2]) % 1_800_000)
    return max(0, anchor - offset_ms)


def build_plain_payload_from_live_result(live_result, detail=None, log_id=None):
    sample = _coerce_jsonish(live_result)
    track = extract_track_from_live_result(sample)
    if track is None:
        raise ValueError("live_result does not contain a usable track/payload object")

    modified_img_width = extract_modified_img_width_from_live_result(sample)
    distance = extract_distance_from_live_result(sample)
    if modified_img_width is None and distance is None:
        raise ValueError("live_result is missing modified_img_width / distance")

    detail, log_id = _extract_detail_and_log_id(sample, detail=detail, log_id=log_id)
    env_util_state = None
    if isinstance(sample, dict):
        env_util_state = _extract_from_candidates(
            sample,
            "envUtilState",
            "finalEnvUtilState",
            "before",
            "after",
        )

    payload = build_plain_payload_base(
        track.get("id", ""),
        modified_img_width=modified_img_width or UI_WIDTH,
        mode=track.get("mode", SUBTYPE_MODE),
        c=track.get("c", PAYLOAD_C),
    )
    payload.update(deepcopy(track))

    payload.setdefault("c", list(PAYLOAD_C))
    payload.setdefault("8uyk1GN", [])
    payload.setdefault("1ZBkmqar4", [])
    payload.setdefault("Q1FvvZeZE", build_compound_track())

    if isinstance(payload.get("env"), dict):
        if detail and log_id and isinstance(payload.get("id"), str):
            payload["env"].setdefault("font_hash", build_font_hash(payload["id"]))
            payload["env"].setdefault("scale", BASE_ENV_TEMPLATE["scale"])
        apply_env_util_state(payload["env"], env_util_state)

    return payload


def build_drag_points(distance, rng):
    elapsed = 0
    current_width = 0
    # Fresh accepted Web/H5 samples cover roughly 36..75 compressed points.
    # Protocol 200s and clean browser payloads both sit mostly in 43..61, with
    # occasional 66+ long drags.  Keep a weighted table instead of a flat range
    # so body size remains in the live 8k..12k band without over-sampling tails.
    step_count = rng.choice(
        [
            # Pure protocol 2026-05-09 successes clustered around 56..59
            # compressed drag points.  Short 38..44 point tracks produced
            # valid-looking captchaBody but were frequently rejected as 5009,
            # so keep them out of the default protocol generator.
            50, 51, 54,
            55, 56, 56, 56, 58, 58, 59, 59, 61,
        ]
    )
    drag_points = []

    for index in range(1, step_count + 1):
        ratio = index / step_count
        eased_ratio = 1 - (1 - ratio) ** rng.uniform(2.05, 2.35)
        wobble = rng.choice([0, 0, 0, 1, -1]) if 0 < index < step_count else 0
        next_width = int(round(distance * eased_ratio)) + wobble
        next_width = max(current_width, min(distance, next_width))
        if index == 1:
            elapsed += rng.randint(3, 18)
        else:
            # Browser-dispatched drags in 1.0.0.759 usually advance at about
            # 45..50 ms per compressed point.  Keep small jitter but avoid the
            # old shorter 34 ms floor that made total drag time too low.
            elapsed += rng.randint(41, 53)
        current_width = next_width
        drag_points.append({"width": current_width, "relative_time": elapsed})

    # Real browser final tracks usually have little/no terminal hold in the
    # compressed 8uyk1GN array.  Keep it rare to avoid bloating captchaBody.
    hold_count = rng.choice([0, 0, 0, 1])
    for _ in range(hold_count):
        elapsed += rng.randint(25, 45)
        drag_points.append({"width": distance, "relative_time": elapsed})

    return drag_points


def build_absolute_drag_track(drag_points, drag_start_x, drag_start_y, base_time, rng):
    drag_absolute = []
    for point in drag_points:
        drag_absolute.append(
            {
                "x": drag_start_x + point["width"],
                "y": drag_start_y + rng.randint(-1, 1),
                "width": point["width"],
                "time": base_time + point["relative_time"],
                "t": 0,
                "relative_time": point["relative_time"],
            }
        )

    sampled_track = [{"x": drag_start_x, "y": drag_start_y, "time": base_time, "t": 0}]
    for point in drag_absolute[::2]:
        sampled_track.append(
            {
                "x": point["x"],
                "y": point["y"],
                "time": point["time"],
                "t": point["t"],
            }
        )
    # Fresh browser rHqT9pMS is consistently ceil(len(8uyk1GN)/2)+1: the
    # initial press plus every other compressed drag point.  If the drag has an
    # even number of points, append the final release position as the last
    # sampled point to avoid being one short.
    if (
            drag_absolute
            and len(drag_absolute) % 2 == 0
            and len(sampled_track) < ((len(drag_absolute) + 1) // 2 + 1)
    ):
        point = drag_absolute[-1]
        sampled_track.append(
            {
                "x": point["x"],
                "y": point["y"],
                "time": point["time"],
                "t": point["t"],
            }
        )
    return drag_absolute, sampled_track


def build_uye_track(press_x, press_y, drag_start_x, drag_start_y, drag_absolute, distance, base_time, drag_points,
                    rng, ):
    uye = [{"x": drag_start_x, "y": drag_start_y, "time": base_time}]
    # Fresh browser J9c keeps most mousemove events but is usually a few points
    # shorter than 8uyk1GN.  Drop a small number of interior near-duplicate
    # moves deterministically to mirror that compacting.
    last_x = drag_start_x
    drop_budget = rng.choice([0, 1, 1, 2, 2, 3, 4, 5])
    for point in drag_absolute[1:]:
        if point["width"] == distance and last_x == drag_start_x + distance and rng.random() < 0.55:
            continue
        if (
                drop_budget > 0
                and len(uye) > 3
                and point is not drag_absolute[-1]
                and rng.random() < 0.065
        ):
            drop_budget -= 1
            last_x = point["x"]
            continue
        uye.append({"x": point["x"], "y": point["y"], "time": point["time"]})
        last_x = point["x"]
    release_time = drag_absolute[-1]["time"] if drag_absolute else base_time
    release_x = drag_start_x + distance
    release_y = drag_start_y
    while len(uye) < 24:
        release_time += rng.randint(45, 75)
        uye.append({"x": release_x, "y": release_y + rng.randint(0, 1), "time": release_time})
    return uye


def build_compound_track(move_track=None, sampled_track=None, press_point=None, drag_entry_point=None):
    return {
        "AGV8DioD": dict(press_point or {}),
        "2MILE": dict(drag_entry_point or {}),
        "J9c": list(move_track or []),
        "FrZXd9GD": [],
        "rHqT9pMS": list(sampled_track or []),
        "pE2N": [],
    }


def build_drag_bundle(distance, tip_y, rng=None):
    rng = rng or random.Random()
    drag_start_x = 54
    drag_start_y = 306
    press_x = drag_start_x
    press_y = drag_start_y
    # In browser final payload, mouse tracks are produced after the challenge
    # has loaded/ready.  Keep track timestamps around the current drag window;
    # build_env() will put loading/ready slightly before this range.
    base_time = int(time.time() * 1000) - rng.randint(80, 180)
    slide_entry_time = base_time

    drag_points = build_drag_points(distance, rng)
    compressed_drag = []
    for point in drag_points:
        compressed_drag.append(
            {
                "x": point["width"],
                "y": tip_y,
                "relative_time": point["relative_time"],
            }
        )

    drag_absolute, sampled_track = build_absolute_drag_track(
        drag_points,
        drag_start_x,
        drag_start_y,
        base_time,
        rng,
    )
    move_track = build_uye_track(
        press_x,
        press_y,
        drag_start_x,
        drag_start_y,
        drag_absolute,
        distance,
        base_time,
        drag_points,
        rng,
    )

    compound_track = build_compound_track(
        move_track=move_track,
        sampled_track=sampled_track,
        press_point={
            "x": press_x,
            "y": press_y,
            "time": slide_entry_time,
        },
        drag_entry_point={
            "x": drag_start_x,
            "y": drag_start_y,
            "time": slide_entry_time,
        },
    )
    # Fresh 1.0.0.759 Web/H5 final wasm.encrypt samples from clean drags
    # carry one compact mouse action marker.  Four markers are retained only
    # by old replay/static samples.
    mouse_actions = ["1,1"]
    return {
        "compressed_drag": compressed_drag,
        "compound_track": compound_track,
        "mouse_actions": mouse_actions,
        "runtime_state": {
            # Live 1.0.0.759 Web samples keep top-level a/b in compact
            # browser-runtime ranges (roughly a=19..70, b=10..52).  The old
            # distance formula forced b>=60 and was outside fresh samples.
            "a": rng.randint(19, 78),
            "b": rng.randint(10, 52),
            "mouse_start_time": move_track[0]["time"] if move_track else base_time,
            "drag_end_time": drag_absolute[-1]["time"] if drag_absolute else base_time,
            "track_end_time": sampled_track[-1]["time"] if sampled_track else base_time,
        },
    }


def build_env(detail, log_id, captcha_id, mouse_actions, rng=None, env_util_state=None, env_overrides=None,
              runtime_state=None):
    rng = rng or random.Random()
    env_overrides = deepcopy(env_overrides or {})
    runtime_state = deepcopy(runtime_state or {})
    timing_mode = str(env_overrides.pop("timing_mode", os.getenv("CAPTCHA_TIMING_MODE", "dynamic"))).lower()
    env = deepcopy(BASE_ENV_TEMPLATE)
    # Fresh browser samples alternate Performance detector value between 0/1.
    try:
        env["detectors"]["Performance"]["value"] = rng.choice([0, 1])
    except Exception:
        pass
    apply_page_env(env, env_overrides)
    font_hash = str(env_overrides.pop("font_hash", "") or build_font_hash(captcha_id))
    env.update(build_env_arrays(detail, log_id, captcha_id, font_hash, env_util_state=env_util_state))
    try:
        for _idx, _row in enumerate(OBSERVED_ENV_FINGERPRINTS_759):
            _c3, _k3, _m_pair, _runtime3 = _row
            if env.get("c", [None, None, None])[2] == _c3[2] and env.get("k") == list(_k3):
                runtime_state["env_bucket_index"] = _idx
                runtime_state.setdefault("env_runtime_values", list(_runtime3))
                break
    except Exception:
        pass
    now = int(time.time() * 1000)
    page_env = extract_page_env(env_overrides)
    page_mask_time = _safe_int(page_env.get("maskTime")) if isinstance(page_env, dict) else None
    has_loading_override = "loading_time" in env_overrides
    has_ready_override = "ready_time" in env_overrides
    has_d_override = "d" in env_overrides
    track_start = _safe_int(runtime_state.get("mouse_start_time"))
    if track_start is not None:
        default_loading = track_start - rng.randint(1500, 2300)
    else:
        default_loading = now - rng.randint(700, 1400)
    loading_time = int(env_overrides.pop("loading_time", default_loading))
    ready_time = int(env_overrides.pop("ready_time", loading_time + rng.randint(240, 430)))
    mask_time_base = resolve_mask_time_base(
        detail,
        log_id,
        captcha_id,
        env_util_state=env_util_state,
        env_overrides=env_overrides,
        loading_time=loading_time,
    )
    has_mask_time_override = "mask_time" in env_overrides
    has_mask_suffix_override = "mask_time_suffix" in env_overrides
    if (
            page_mask_time is not None
            and not has_mask_suffix_override
            and not has_mask_time_override
            and not isinstance(env_util_state, dict)
            and timing_mode in {"sample759", "static_sample", "replay_sample"}
    ):
        # Clean 1.0.0.759 H5 final encrypt sample:
        #   query env.maskTime=1778165411620
        #   payload.env.mask_time=177816541162059
        # Keep explicit overrides/env_util_state taking precedence.  This mode
        # is only for replaying the captured sample; live protocol generation
        # must keep timing dynamic.
        mask_suffix = 59
    else:
        mask_suffix = int(
            env_overrides.pop(
                "mask_time_suffix",
                derive_mask_time_suffix(
                    detail,
                    log_id,
                    captcha_id,
                    ready_time=ready_time,
                    runtime_state=runtime_state,
                ),
            )
        )
    mask_time = int(env_overrides.pop("mask_time", mask_time_base * 100 + mask_suffix))
    inherited_mouse_actions = _extract_state_actions(env_util_state) or []
    override_mouse_actions = env_overrides.pop("mouse_actions", None)
    if override_mouse_actions is None:
        default_mouse_actions = inherited_mouse_actions + list(mouse_actions or [])
    else:
        default_mouse_actions = list(override_mouse_actions)

    inherited_d = _extract_state_int(env_util_state, "d")
    inherited_f = _extract_state_int(env_util_state, "f")
    inherited_fps = _extract_state_int(env_util_state, "fps")
    inherited_g = _extract_state_int(env_util_state, "g")

    if default_mouse_actions:
        bucket = None
        runtime_values = runtime_state.get("env_runtime_values")
        if isinstance(runtime_values, (list, tuple)) and len(runtime_values) >= 3:
            bucket = tuple(runtime_values[:3])
        else:
            bucket_index = runtime_state.get("env_bucket_index")
            if isinstance(bucket_index, int) and 0 <= bucket_index < len(OBSERVED_ENV_FINGERPRINTS_759):
                bucket = OBSERVED_ENV_FINGERPRINTS_759[bucket_index][3]
        default_f = int(
            env_overrides.pop("f", inherited_f if inherited_f is not None else (bucket[0] if bucket else rng.choice(OBSERVED_F_VALUES)))
        )
        default_fps = int(
            env_overrides.pop("fps", inherited_fps if inherited_fps is not None else (bucket[1] if bucket else rng.choice(OBSERVED_FPS_VALUES)))
        )
        default_g = int(
            env_overrides.pop("g", inherited_g if inherited_g is not None else (bucket[2] if bucket else rng.choice(OBSERVED_G_VALUES)))
        )
    else:
        default_f = int(env_overrides.pop("f", inherited_f if inherited_f is not None else 5))
        default_fps = int(env_overrides.pop("fps", inherited_fps if inherited_fps is not None else 2))
        default_g = int(env_overrides.pop("g", inherited_g if inherited_g is not None else 12))
    default_d = int(
        env_overrides.pop(
            "d",
            inherited_d if inherited_d is not None else ready_time + rng.choice(OBSERVED_D_DELTAS),
        )
    )

    env.update(
        {
            "font_hash": font_hash,
            "mouse_actions": default_mouse_actions,
            "d": default_d,
            "f": default_f,
            "fps": default_fps,
            "mask_time": mask_time,
            "loading_time": loading_time,
            "ready_time": ready_time,
            "g": default_g,
            "o": _derive_o_values(default_mouse_actions),
        }
    )
    # sample759/static_sample is a replay-only mode for the captured H5 sample.
    # The default live path keeps loading/ready/d/mask suffix dynamic; otherwise
    # repeated protocol attempts carry the same old 1778165411620xx timing and
    # are easy to reject by strict timing checks.
    if (
            page_mask_time is not None
            and not any((has_loading_override, has_ready_override, has_d_override))
            and not isinstance(env_util_state, dict)
            and timing_mode in {"sample759", "static_sample", "replay_sample"}
    ):
        env["loading_time"] = page_mask_time + 4_414_382
        env["ready_time"] = env["loading_time"] + 288
        env["d"] = env["ready_time"] + 11
    if isinstance(env.get("m"), list) and len(env["m"]) >= 3:
        env["m"][2] = _derive_m_suffix(env.get("k"), default_mouse_actions, env.get("font_hash"))
    # README 8.3 used n=c2+15/o=[8] for the older 739 resource.  Fresh
    # 1.0.0.759 Web/H5 payloads differ here: c[4]=10, n=c2+12, o=[4].
    apply_env_util_state(env, env_util_state)
    if env_overrides:
        env.update(env_overrides)
    return env


def build_plain_payload_base(captcha_id, *, modified_img_width=UI_WIDTH, mode=SUBTYPE_MODE, c=None):
    return {
        "modified_img_width": int(modified_img_width),
        "id": captcha_id,
        "mode": mode,
        "c": list(c or PAYLOAD_C),
    }


def build_generated_plain_payload(
        captcha_id,
        distance,
        tip_y,
        detail,
        log_id,
        *,
        env_util_state=None,
        env_overrides=None,
        runtime_overrides=None,
):
    runtime_overrides = deepcopy(runtime_overrides or {})
    payload_template = extract_payload_template(runtime_overrides.pop("payload_template", None), captcha_id=captcha_id)
    drag_bundle = build_drag_bundle(distance, tip_y)
    runtime_state = drag_bundle["runtime_state"]
    env = build_env(
        detail,
        log_id,
        captcha_id,
        drag_bundle["mouse_actions"],
        env_util_state=env_util_state,
        env_overrides=env_overrides,
        runtime_state=runtime_state,
    )

    payload = build_plain_payload_base(
        captcha_id,
        modified_img_width=runtime_overrides.pop("modified_img_width", UI_WIDTH),
    )
    payload.update(
        {
            "8uyk1GN": runtime_overrides.pop("8uyk1GN", drag_bundle["compressed_drag"]),
            "1ZBkmqar4": runtime_overrides.pop("1ZBkmqar4", []),
            "Q1FvvZeZE": runtime_overrides.pop("Q1FvvZeZE", drag_bundle["compound_track"]),
            "env": env,
            "a": runtime_overrides.pop("a", runtime_state["a"]),
            "b": runtime_overrides.pop("b", runtime_state["b"]),
        }
    )
    apply_payload_template(payload, payload_template)
    return payload


def build_plain_payload(
        captcha_id,
        distance,
        tip_y,
        detail,
        log_id,
        *,
        live_result=None,
        env_util_state=None,
        env_overrides=None,
        runtime_overrides=None,
):
    if live_result is not None:
        return build_plain_payload_from_live_result(live_result, detail=detail, log_id=log_id)

    return build_generated_plain_payload(
        captcha_id,
        distance,
        tip_y,
        detail,
        log_id,
        env_util_state=env_util_state,
        env_overrides=env_overrides,
        runtime_overrides=runtime_overrides,
    )
