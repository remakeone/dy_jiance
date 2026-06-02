# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
ZWJ = "\u200d"


def _resolve_script_path() -> Path:
    current_dir = Path(__file__).resolve().parent
    candidates = (
        current_dir / "run_vm_wasm_node.js",
        ROOT / "probe" / "run_vm_wasm_node.js",
        ROOT / "captchabody" / "run_vm_wasm_node.js",
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


SCRIPT_PATH = _resolve_script_path()


class CaptchaBodyError(RuntimeError):
    pass


def _build_json_error_message(stdout: str, error: json.JSONDecodeError) -> str:
    start = max(0, error.pos - 120)
    end = min(len(stdout), error.pos + 120)
    excerpt = stdout[start:end].replace("\n", "\\n")
    return f"invalid JSON output: {error}; excerpt={excerpt}"


def generate_captcha_result(
        payload: str | dict[str, Any],
        *,
        page_url: str | None = None,
        detail: str | None = None,
        seed: int | None = None,
        order: list[int] | tuple[int, ...] | None = None,
        chrome_path: str | None = None,
        cwd: str | Path | None = None,
        timeout: float = 90.0,
        runtime: str | None = None,
) -> dict[str, Any]:
    payload_options: dict[str, Any] = {}
    if isinstance(payload, str):
        payload_text = payload
    else:
        # Internal runner options are allowed on the Python object but must not
        # leak into the captchaBody plaintext JSON.
        payload_options = {
            key: payload.get(key)
            for key in ("__tag_y_mode", "_tag_y_mode", "__fixed_now", "_fixed_now")
            if payload.get(key) is not None
        }
        clean_payload = {
            key: value for key, value in payload.items()
            if key not in payload_options
        }
        payload_text = json.dumps(clean_payload, separators=(",", ":"), ensure_ascii=False)

    payload_file_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                suffix=".json",
                delete=False,
        ) as payload_file:
            payload_file.write(payload_text)
            payload_file_path = Path(payload_file.name)

        cmd = [
            "node",
            str(SCRIPT_PATH),
            f"--payload-file={payload_file_path}",
            "--output=json",
        ]
        if page_url:
            cmd.append(f"--page-url={page_url}")
        if detail:
            cmd.append(f"--detail={detail}")
        if seed is not None:
            cmd.append(f"--seed={int(seed)}")
        if order:
            cmd.append("--order=" + ",".join(str(int(item)) for item in order))
        if chrome_path:
            cmd.append(f"--chrome-path={chrome_path}")
        if runtime:
            cmd.append(f"--runtime={runtime}")
        tag_y_mode = payload_options.get("__tag_y_mode") or payload_options.get("_tag_y_mode")
        tag_y_mode = tag_y_mode or os.environ.get("CAPTCHA_TAG_Y_MODE")
        if tag_y_mode:
            cmd.append(f"--tag-y-mode={tag_y_mode}")
        fixed_now = payload_options.get("__fixed_now") or payload_options.get("_fixed_now")
        fixed_now = fixed_now or os.environ.get("CAPTCHA_FIXED_NOW")
        if fixed_now:
            cmd.append(f"--fixed-now={fixed_now}")

        completed = subprocess.run(
            cmd,
            cwd=str(cwd or ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    finally:
        if payload_file_path is not None:
            payload_file_path.unlink(missing_ok=True)

    if completed.returncode != 0:
        raise CaptchaBodyError(
            completed.stderr.strip() or completed.stdout.strip() or "node script failed"
        )

    stdout = completed.stdout.strip()
    if not stdout:
        raise CaptchaBodyError("node script returned empty output")

    try:
        result = json.loads(stdout)
    except json.JSONDecodeError as error:
        raise CaptchaBodyError(_build_json_error_message(stdout, error)) from error

    if "captchaBody" not in result:
        raise CaptchaBodyError(f"captchaBody is missing in output: {result}")

    return result


def generate_captcha_body(
        payload: str | dict[str, Any],
        **kwargs: Any,
) -> str:
    return str(generate_captcha_result(payload, **kwargs)["captchaBody"])

