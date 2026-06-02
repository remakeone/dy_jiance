import urllib

import requests

from module.six_god2.core import sign_android
from module.six_god2.抖音设备注册 import encrypt_tt

def xor(s):
    chars = '0123456789abcdef'
    arr = [i ^ 5 for i in s.encode()]
    result = ''
    for b in arr:
        result += chars[(b & 255) >> 4]
        result += chars[(b & 255) & 15]
    return result


url = "https://api5-normal-c-lq.amemv.com/passport/mobile/send_code/"
params = {
    "passport-sdk-version": "601441",
    "request_from_account_sdk": "1",
    "is_from_ttaccountsdk": "1",
    "iid": "1206602207631129",
    "device_id": "1206602207627033",
    "ac": "wifi",
    "channel": "50067829a",
    "aid": "1349",
    "app_name": "maya",
    "version_code": "370300",
    "version_name": "37.3.0",
    "device_platform": "android",
    "os": "android",
    "ssmix": "a",
    "device_type": "OPPO A4",
    "device_brand": "OPPO",
    "language": "zh",
    "os_api": "33",
    "os_version": "13",
    "manifest_version_code": "370301",
    "resolution": "1080*2132",
    "dpi": "450",
    "update_version_code": "37309900",
    "_rticket": "1767971240134",
    "package": "my.maya.android",
    "first_launch_timestamp": "1767902260",
    "last_deeplink_update_version_code": "0",
    "cpu_support64": "true",
    "host_abi": "arm64-v8a",
    "is_guest_mode": "0",
    "app_type": "normal",
    "minor_status": "0",
    "appTheme": "light",
    "is_preinstall": "0",
    "need_personal_recommend": "1",
    "is_android_pad": "0",
    "is_android_fold": "0",
    "ts": "1767971238",
    "cdid": "ad912f30-784b-4146-ade6-ecfd96d64d65",
    "cronet_version": "6f1e308d_2025-12-08",
    "ttnet_version": "4.2.243.28-douyin",
    "use_store_region_cookie": "1"
}
payload = {
    "is_vcd": "0",
    "reg_cookie_opt": "true",
    "auto_read": "0",
    "account_sdk_source": "app",
    "passport_support_flow": "choose_account,captcha,real_name_check,verify",
    "unbind_exist": "35",
    "mix_mode": "1",
    "mobile": xor("+1 12637008184"),
    "is_from_iesaccountsaas": "1",
    "multi_login": "1",
    "type": "31"
}
payload = encrypt_tt(urllib.parse.urlencode(payload))

headers = {
    'User-Agent': "my.maya.android/370301 (Linux; U; Android 13; zh_CN; OPPO A4; Build/TQ3A.230705.001; Cronet/TTNetVersion:6f1e308d 2025-12-08 QuicVersion:21ac1950 2025-11-18)",
    'Content-Type': "application/octet-stream",
    'log-encode-type': "gzip",
    'x-tt-request-tag': "t=0;n=1;s=0;p=0",
    'activity_now_client': "0",
    'x-ss-req-ticket': "1767902262953",
    'sdk-version': "2",
    'passport-sdk-version': "601441",
    'x-vc-bdturing-sdk-version': "4.1.1.cn",
    'content-type': "application/octet-stream;tt-data=a",
    'x-ss-stub': "56AE8287A429F36CC6DB3768BD4B0912",
    'x-ss-dp': "1349",
    'x-tt-trace-id': "00-9f2fb879010683974439016a76600545-9f2fb87901068397-01",
    # 'x-argus': "NwxgaQ==",
    # 'x-gorgon': "840430300000c1940d635adb9d462406d5ba36e2874707d20f9e",
    # 'x-helios': "B0+ldPBNMW3a5DRZ+QBZvp3seeGkQPu8jqW2QUXDz5focKtk",
    # 'x-khronos': "1767902263",
    # 'x-ladon': "+v8uFQ==",
    # 'x-medusa': "MgxgaRpHL6N+eW0qCLnORRVhrD9S+wABQOE7oIFugeAKGHO6ascQY+XdNoLAXGu2p5JOiitwwIBXO+S41tsn40vsleG2B0EotkudV3e3LTPPMVAtr5gq7m4ADqU23UJiRadQpStIO/rxwIfBAckbwrQLA8MIERboAjsHPS9iVTmU/v79HP9P/LTDdgan90df21CnpNnsKt1r1GT6IK2Ip0Lhi76J1B5KhaUXIK3n45jBLgM0G3p11sFIuI+b7gLD95G6ZE2lQ0AhTSoa2ZwMZQ13onErzjJMQwhp7Yb/R6kE/Zh7N1xi8334aDwB2bsFBjjAqUdThYv8vGx6ehXCYMohv/7QVnPuEg0tR5eRqlefn9C2Uy6cdq8s2t4jeuHPPHNn5UxwdVIjykP3cnCLhUvXrv4eWwUhx/7mnu5GHqNKjK3Dxyd5KQrvqy2pcNWNJ2i7ygXdg4KQAT/6hFzdPXbf9itrMSuxKebsCH+KiodY9fUAUMecyLYFbQ2p7YLtF0Fjr5QQ3HC10eYFjmKPtzhsDiP6aYF+hRqd1x31AE1CDmTtHyPOh3FZCEdHpgGikbZhbJ2IGx8xI/MP9wnmf1w7XQ4lcurIACV5L6KuzexUJ+8qV0QKawibo9b4/O5x9C/9rdQR70QYDOJfuLMMf3a6sMZagjzBRQoWNGIuvb4BEnXMz6MCiA2qIhAjx7VYOF2rHRIO4xLD4V57SXoKzsGg96U2h/kLCXBb7Eg/RJROURjFujMogfylsJaw1gPl9jy6LHyOF5tmXGazXQdGHhXN+HSUEx/zaUG4fRaNZbIldcAPwQXCH7HzdTbPFHCTnWD3oYSsr+xlU0kZwGeokgI9k0j9odCAzPeXI6F8AdBx52A5dbjU/vxdFFEKLplRI+Qb8gyl3NojVobn2LI7nfD51gzJawCPVHtD1BAVPf2XDTdAmLG27JRE7/CEiUMowdvxtEboozsjqrKq8f00d+4dXyyDbdAGZsKucq3hF4+EKMFYvqSp2PdAWTYzKLKa5pHdW1oMxssVZCjCSu13bb477xryMJcUOI0JwZ/258JLX5RLRqOvUvrOo1f6U2P6vxn/+r8Z/6hL",
    # 'Cookie': "passport_csrf_token=b9388a7ca9d2eccb604d7a244f0f1b19; passport_csrf_token_default=b9388a7ca9d2eccb604d7a244f0f1b19"
}
headers = {
    "Host": "api5-normal-c-lq.amemv.com",
    "sdk-version": "2",
    'x-vc-bdturing-sdk-version': "4.1.1.cn",
    'User-Agent': "my.maya.android/370301 (Linux; U; Android 13; zh_CN; OPPO A4; Build/TQ3A.230705.001; Cronet/TTNetVersion:6f1e308d 2025-12-08 QuicVersion:21ac1950 2025-11-18)",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "content-length": "178"
}
sign_headers, sign_urls = sign_android(url=url, params=params, data=payload, header=headers, cell=True, log=False)
# response = requests.post(sign_urls, data=payload, headers=headers, proxies={}, timeout=30, verify=False)
print(sign_headers)
response = requests.post(url, data=payload, headers=headers, proxies={
    # "http": "http://14.18.125.37:34768",
    # "https": "http://14.18.125.37:34768",
})

print(response.text)