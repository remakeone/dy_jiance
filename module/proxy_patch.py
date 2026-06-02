# -*- coding: utf-8 -*-
"""
方法：requests 猴子补丁，将所有 HTTP 请求统一转发到代理服务器
说明：
    - 通过替换 requests.Session.request 实现拦截
    - 通过环境变量控制开关与代理地址
    - 失败时回退到原始直连请求，保障可用性
环境变量：
    PROXY_ENABLED   -> true/false 是否启用代理
    PROXY_BASE_URL  -> http://host:port/proxy 代理服务器接口地址
    PROXY_SIGN_SECRET -> 预留签名密钥（示例未实现签名逻辑）
"""
import os
import time
import base64
import json
import uuid
import requests
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple, Union

# 重要：保存原始实现，便于回退
_ORIGINAL_SESSION_REQUEST = requests.Session.request

def _is_enabled() -> bool:
    """
    方法：判断是否启用代理转发（猴子补丁）
    说明：通过环境变量 PROXY_ENABLED 控制，默认 False。
    """
    return os.environ.get("PROXY_ENABLED", "false").lower() in ("1", "true", "yes", "on")

def _proxy_url() -> str:
    """
    方法：获取转发服务器的 /proxy 完整地址
    说明：通过环境变量 PROXY_BASE_URL 提供，必须以 /proxy 结尾。
    """
    url = os.environ.get("PROXY_BASE_URL", "").strip()
    if not url:
        raise RuntimeError("未设置 PROXY_BASE_URL，无法使用代理转发")
    return url

def _b64_encode_bytes(data: bytes) -> str:
    """
    方法：对二进制数据进行 Base64 编码
    说明：用于将请求体或文件内容安全封装到 JSON 中。
    """
    return base64.b64encode(data).decode("ascii")

def _pick_text_or_b64(content: bytes) -> Dict[str, Optional[str]]:
    """
    方法：根据内容类型选择返回 bodyText 或 bodyBase64
    说明：如果可解码为 UTF-8 文本，优先使用 bodyText，否则使用 bodyBase64。
    """
    try:
        return {"bodyText": content.decode("utf-8"), "bodyBase64": None}
    except UnicodeDecodeError:
        return {"bodyText": None, "bodyBase64": _b64_encode_bytes(content)}

def _normalize_files(files: Optional[
    Union[Mapping[str, Union[Tuple[str, Any, Optional[str]], Tuple[str, Any]]],
          Iterable[Tuple[str, Union[Tuple[str, Any, Optional[str]], Tuple[str, Any]]]]]
]) -> Optional[Dict[str, Any]]:
    """
    方法：将 requests 的 files 参数转换为可 JSON 序列化结构
    参数：
        files：requests 兼容的 files 参数形式
    返回：
        标准 JSON 结构：
        {
          "files": {
            "field": [
              {"filename": "...", "contentType": "mime/...", "contentB64": "..."},
              ...
            ]
          }
        }
    说明：
        - 支持常见 tuple 形式：(filename, fileobj[, content-type])
        - fileobj 若为 bytes/bytearray/str/path-like，需要读为 bytes
        - 服务端将据此重建 multipart 文件上传
    """
    if files is None:
        return None

    def to_list_of_tuples(maybe_mapping_or_iterable):
        if isinstance(maybe_mapping_or_iterable, Mapping):
            for k, v in maybe_mapping_or_iterable.items():
                if isinstance(v, (list, tuple)) and v and isinstance(v[0], tuple):
                    # dict[field] = [(filename, fileobj[, content-type]), ...]
                    for item in v:
                        yield (k, item)
                else:
                    # dict[field] = (filename, fileobj[, content-type])
                    yield (k, v)
        else:
            # iterable of (field, (filename, fileobj[, content-type]))
            for k, v in maybe_mapping_or_iterable:
                yield (k, v)

    normalized: Dict[str, Any] = {"files": {}}
    for field, value in to_list_of_tuples(files):
        if not isinstance(value, (list, tuple)):
            raise TypeError("files 的条目必须是 tuple 形式")
        if len(value) < 2:
            raise TypeError("files 的条目至少包含 (filename, fileobj)")
        filename = value[0]
        fileobj = value[1]
        content_type = value[2] if len(value) >= 3 else None

        # 读取 fileobj 为 bytes
        if hasattr(fileobj, "read"):
            content_bytes = fileobj.read()
        elif isinstance(fileobj, (bytes, bytearray)):
            content_bytes = bytes(fileobj)
        elif isinstance(fileobj, str):
            # 将字符串视作文本内容
            content_bytes = fileobj.encode("utf-8")
        else:
            # 尝试 path-like
            try:
                with open(fileobj, "rb") as f:
                    content_bytes = f.read()
            except Exception as _:
                raise TypeError("无法识别的 fileobj 类型")

        entry = {
            "filename": filename,
            "contentType": content_type,
            "contentB64": _b64_encode_bytes(content_bytes),
        }
        normalized["files"].setdefault(field, []).append(entry)
    return normalized

def _filter_hop_by_hop_headers(headers: Mapping[str, str]) -> Dict[str, str]:
    """
    方法：过滤 hop-by-hop 头（不应跨节点转发）
    说明：保持端到端头部更干净，避免无效或冲突头。
    """
    hop_by_hop = {
        "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
        "te", "trailers", "transfer-encoding", "upgrade"
    }
    return {k: v for k, v in headers.items() if k.lower() not in hop_by_hop}

def _build_proxy_payload(
    method: str,
    url: str,
    *,
    params: Optional[Mapping[str, Any]],
    data: Optional[Union[bytes, str, Mapping[str, Any]]],
    json_body: Optional[Any],
    headers: Optional[Mapping[str, str]],
    files: Optional[Any],
    timeout: Optional[Union[float, Tuple[float, float]]],
    allow_redirects: Optional[bool],
    stream: bool,
    verify: Union[bool, str, None],
    proxies: Optional[Mapping[str, str]],
) -> Dict[str, Any]:
    """
    方法：构造发送给转发服务器的标准请求载荷
    说明：统一将各种请求参数标准化，便于服务端还原。
    """
    headers = headers or {}
    safe_headers = _filter_hop_by_hop_headers(headers)
    request_id = str(uuid.uuid4())

    # 处理 data/json 二选一优先：若传入 json_body 则忽略 data
    data_text = None
    data_b64 = None
    if json_body is not None:
        pass  # 服务端会用 json 字段
    else:
        if data is None:
            pass
        elif isinstance(data, (bytes, bytearray)):
            data_b64 = _b64_encode_bytes(bytes(data))
        elif isinstance(data, str):
            data_text = data
        elif isinstance(data, Mapping):
            # 表单 data，交给服务端按表单转发（使用 form 字段）
            pass
        else:
            # 其他类型统一转 bytes
            data_b64 = _b64_encode_bytes(bytes(data))

    files_payload = _normalize_files(files)

    # 统一的 JSON 载荷
    payload: Dict[str, Any] = {
        "requestId": request_id,
        "method": method.upper(),
        "url": url,
        "headers": dict(safe_headers),
        "params": dict(params or {}),
        "json": json_body,
        "form": dict(data) if isinstance(data, Mapping) else None,
        "dataText": data_text,
        "dataBase64": data_b64,
        "files": files_payload["files"] if files_payload else None,
        # cookies 将在 _session_request_proxy 中注入
        "timeoutMs": int((timeout if isinstance(timeout, (int, float)) else (timeout[0] if isinstance(timeout, tuple) else 30.0)) * 1000) if timeout else 30000,
        "proxyOptions": {
            "followRedirects": True if allow_redirects is None else bool(allow_redirects),
            "stream": bool(stream),
            "verify": verify if verify is not None else True,
            "useProxies": bool(proxies),
            "proxies": dict(proxies or {}),
        },
    }

    # 可选签名（示例预留，实际可用 HMAC）
    sign_secret = os.environ.get("PROXY_SIGN_SECRET", "")
    if sign_secret:
        payload["signature"] = "not-implemented"  # 可自定义签名
        payload["timestamp"] = int(time.time())

    return payload

def _build_response_from_proxy(resp_json: Mapping[str, Any]) -> requests.Response:
    """
    方法：从转发服务器返回的 JSON 构建 requests.Response 对象
    说明：尽量还原 requests 的行为，让上层无感知。
    """
    r = requests.Response()
    r.status_code = int(resp_json.get("status", 502))
    r.headers = requests.structures.CaseInsensitiveDict(resp_json.get("headers", {}) or {})
    r.url = resp_json.get("finalUrl") or resp_json.get("url") or ""
    r.reason = resp_json.get("reason") or ""
    body_text = resp_json.get("bodyText")
    body_b64 = resp_json.get("bodyBase64")
    if body_text is not None:
        r._content = body_text.encode("utf-8")
        r.encoding = "utf-8"
    elif body_b64 is not None:
        r._content = base64.b64decode(body_b64)
    else:
        r._content = b""
    # 耗时信息（非必须）
    try:
        from datetime import timedelta
        r.elapsed = timedelta(milliseconds=int(resp_json.get("elapsedMs", 0)))
    except Exception:
        pass
    return r

def _proxy_call(payload: Dict[str, Any]) -> Mapping[str, Any]:
    """
    方法：调用转发服务器 /proxy 接口
    说明：使用原始 requests（避免递归拦截），并处理错误兜底。
    """
    proxy_endpoint = _proxy_url()
    headers = {"Content-Type": "application/json"}
    # 使用原始 Session.request 防止递归
    session = requests.Session()
    # print(f"Calling proxy endpoint: {proxy_endpoint} with payload: {payload}")
    resp = _ORIGINAL_SESSION_REQUEST(
        session, "POST", proxy_endpoint,
        data=json.dumps(payload),
        headers=headers,
        timeout=max(5.0, (payload.get("timeoutMs", 30000) / 1000.0) + 5.0),
        allow_redirects=False,
    )
    resp.raise_for_status()
    return resp.json()

def _session_request_proxy(
    self,
    method: str,
    url: str,
    **kwargs: Any,
) -> requests.Response:
    """
    方法：替换 requests.Session.request 的代理实现
    参数：
        method, url：请求方法与 URL
        kwargs：与 requests 兼容的可选参数（params, data, json, headers, files, timeout, allow_redirects, stream, verify, proxies 等）
    返回：
        requests.Response：从转发服务器返回信息还原的响应对象
    说明：
        - 当 PROXY_ENABLED=false 时，自动回退至原始实现，不影响原逻辑。
        - 建议尽量避免在极早阶段以外重复打补丁。
    """
    if not _is_enabled():
        return _ORIGINAL_SESSION_REQUEST(self, method, url, **kwargs)
    if 'paojiaoyun.com' in url:
        return _ORIGINAL_SESSION_REQUEST(self, method, url, **kwargs)

    # 收集常见参数
    params = kwargs.get("params")
    data = kwargs.get("data")
    json_body = kwargs.get("json")
    headers = kwargs.get("headers")
    files = kwargs.get("files")
    cookies = kwargs.get("cookies")
    timeout = kwargs.get("timeout")
    allow_redirects = kwargs.get("allow_redirects", True)
    stream = kwargs.get("stream", False)
    verify = kwargs.get("verify", True)
    proxies = kwargs.get("proxies")

    # 关键代码段：收集未识别的其它参数，避免遗漏
    known_keys = {"params","data","json","headers","files","cookies","timeout","allow_redirects","stream","verify","proxies","auth","hooks"}
    extra_kwargs = {k: v for k, v in kwargs.items() if k not in known_keys}
    # print(url)
    payload = _build_proxy_payload(
        method, url,
        params=params, data=data, json_body=json_body, headers=headers, files=files,
        timeout=timeout, allow_redirects=allow_redirects, stream=stream,
        verify=verify, proxies=proxies,
    )

    # 方法：合并 Session 级与本次调用的 cookies
    try:
        merged_cookies: Dict[str, Any] = {}
        # Session 中的 cookies
        if hasattr(self, "cookies") and self.cookies is not None:
            for k in self.cookies.keys():
                merged_cookies[k] = self.cookies.get(k)
        # 调用时传入的 cookies 覆盖同名项
        if isinstance(cookies, Mapping):
            for k, v in cookies.items():
                merged_cookies[k] = v
        if merged_cookies:
            payload["cookies"] = merged_cookies
    except Exception:
        pass

    try:
        resp_json = _proxy_call(payload)
    except Exception as e:
        # 关键代码段：代理失败时的容错处理
        # 说明：为保障可用性，失败时回退直连；也可改为抛出异常。
        print(e)
        raise e
        # return _ORIGINAL_SESSION_REQUEST(self, method, url, **kwargs)

    resp = _build_response_from_proxy(resp_json)

    # 方法：写回响应 cookies 到 Response 对象
    try:
        resp_cookies = resp_json.get("cookies") or {}
        if isinstance(resp_cookies, Mapping):
            for k, v in resp_cookies.items():
                try:
                    resp.cookies.set(k, v)
                except Exception:
                    pass
    except Exception:
        pass

    return resp

# 关键代码段：打补丁（全局生效）
# 说明：必须位于项目中最早的导入阶段（早于任何发起请求的代码）
if _is_enabled():
    requests.Session.request = _session_request_proxy


