import requests
from flurl.core import core_sixgod


def toke_phone_num(phone_num):
    bytes_phone_number_data = phone_num.encode("utf-8")
    xor_bytes = bytes([byte ^ 5 for byte in bytes_phone_number_data])
    # 逐字节转换为十六进制字符串并拼接
    hex_string = ''.join(format(byte, '02x') for byte in xor_bytes)
    return hex_string

def email_signup(dev,mail,code,uuid_without_dashes,proxy=None):
    # code = '762753'
    end_code = toke_phone_num(code)
    # mail = 'wrapks97@86mail.cc'
    email_code = toke_phone_num(mail)

    # 拼接发送请求的 url
    url = "https://api3-normal-c-lq.amemv.com/passport/email/quick_login/"

    params = {
        "passport-sdk-version": "601431",
        "request_from_account_sdk": "1",
        "is_from_ttaccountsdk": "1",
        "iid": dev["iid"],
        "device_id": dev["device_id"],
        "ac": dev["device_id"],
        "channel": "googlePlay",
        "aid": dev["aid"],
        "app_name": dev["app_name"],
        "version_code": "370100",
        "version_name": "37.1.0",
        "device_platform": "android",
        "os": "android",
        "ssmix": "a",
        "device_type": dev["device_type"],
        "device_brand": dev["device_brand"],
        "language": "zh",
        "os_api": dev["os_api"],
        "os_version": dev["os_version"],
        "manifest_version_code": "370100",
        "resolution": dev["resolution"],
        "dpi": dev["dpi"],
        "update_version_code": "37109900",
        "_rticket": "1770624661352",
        "package": "com.ss.android.ugc.aweme.mobile",
        "first_launch_timestamp": "1766049783",
        "last_deeplink_update_version_code": "0",
        "cpu_support64": "true",
        "host_abi": dev["host_abi"],
        "is_guest_mode": "0",
        "app_type": "normal",
        "minor_status": "0",
        "appTheme": "light",
        "is_preinstall": "0",
        "need_personal_recommend": "1",
        "is_android_pad": "0",
        "is_android_fold": "0",
        "ts": "1770624658",
        "cdid": dev["cdid"],
        "md": "0",
        "cronet_version": "b9c3e521_2025-09-09",
        "ttnet_version": "4.2.243.16-douyin",
        "use_store_region_cookie": "1"
    }

    headers = {
        # ":method": "POST",
        # ":authority": "api3-normal-c-lq.amemv.com",
        # ":path": "/passport/email/quick_login/?passport-sdk-version=601431&request_from_account_sdk=1&is_from_ttaccountsdk=1&iid=7604774384485746213&device_id=2051038435907593&ac=wifi&channel=googlePlay&aid=1128&app_name=aweme&version_code=370100&version_name=37.1.0&device_platform=android&os=android&ssmix=a&device_type=OPPO+A4&device_brand=OPPO&language=zh&os_api=33&os_version=13&manifest_version_code=370100&resolution=1080*2132&dpi=450&update_version_code=37109900&_rticket=1770624661352&package=com.ss.android.ugc.aweme.mobile&first_launch_timestamp=1766049783&last_deeplink_update_version_code=0&cpu_support64=true&host_abi=arm64-v8a&is_guest_mode=0&app_type=normal&minor_status=0&appTheme=light&is_preinstall=0&need_personal_recommend=1&is_android_pad=0&is_android_fold=0&ts=1770624658&cdid=c85ccce4-d2fa-49b4-8ebb-08d3ecaa5392&md=0&cronet_version=b9c3e521_2025-09-09&ttnet_version=4.2.243.16-douyin&use_store_region_cookie=1",
        # ":scheme": "https",
        # "content-length": "299",
        # "cookie": "ttreq=1$5d2ed25398d796fc11961d1bf9b034f0a256823f",
        # "x-tt-passport-csrf-token": "b224627dccef94606c9aeac84d0cb414",
        # "x-tt-dt": "AAA27EDINIESDZL6JZAWV47GMZYVNPJRIRWHL3TXUOOKAFN7KH52J5M7MHH4AYSMQNXMFJFOLWZXGPQGSKQJA5U6ZZTHUSLPMWVEJGO4J4XIKSMO73OJUAKWDVILI",
        "activity_now_client": "1770624660222",
        "x-ss-req-ticket": "1770624661354",
        "bd-ticket-guard-display-os-version": "TQ3A.230705.001",
        # "bd-ticket-guard-ree-public-key": "BGlj0nh7FkMzE3yj+SoDtJL5je3nDX82ICsaEaybgIoRxoBvCiVXV3gXPy6qaljlJboSMYKo3bxOfwtoxZJEDOg=",
        "bd-ticket-guard-version": "3",
        "passport-sdk-settings": "x-tt-token,sec_user_id",
        "passport-sdk-sign": "x-tt-token,sec_user_id",
        "bd-ticket-guard-tee-status": "1",
        "sdk-version": "2",
        "bd-ticket-guard-iteration-version": "2",
        # "bd-ticket-guard-client-cert": "cHViLkJHb2U1bWkwUC9IazJZQ2xoeHlzbnNmWXJmSlhMTWtwMC9HNi9wZHQyQ0swVktrZm5rZGFWTytJM1M1SVc0VjdaVlVVcFpZUU94alVjQWxUSTJ3d0VGVT0=",
        # "bd-ticket-guard-server-cert-sn": "533240336124694022040808462028007165443034493949",
        "x-tt-passport-trace-id": f"login_{uuid_without_dashes}",
        # "x-tt-passport-verify-portrait": "14617606-545c-418a-9019-e63fc588ef7f.login",
        "passport-sdk-version": "601431",
        "x-vc-bdturing-sdk-version": "4.1.1.cn",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        # "x-ss-stub": "B5EF2D7D77671E138AFAED3A0B666A58",
        # "x-bd-content-encoding": "zstd",
        "x-tt-request-tag": "s=0;p=0",
        "x-ss-dp": "1128",
        # "x-tt-trace-id": "00-4174391b0d7496899649809f21910468-4174391b0d749689-01",
        "User-agent": "com.ss.android.ugc.aweme.mobile/370100 (Linux; U; Android 13; zh_CN; OPPO A4; Build/TQ3A.230705.001; Cronet/TTNetVersion:6f1e308d 2025-12-08 QuicVersion:21ac1950 2025-11-18)",
        # "accept-encoding": "gzip, deflate, br"
        # "x-argus": "lZaJaQ==",
        # "x-gorgon": "8404106c000014c648e6357ec2b8c767e7f3160b98ff603a9488",
        # "x-helios": "qwiJdDgFsLJIcz8bqASdGdvvqUCC8bXL67KE88RyNfu23lgZ",
        # "x-khronos": "1770624661",
        # "x-ladon": "y8P4Xg==",
        # "x-medusa": "kJaJabjdxqPc44QqqiMnRbf7RT+0CAABUzUKig5wAb4FGP2WeBz+hIwH6uXBiSpa9+VxJl5SIbF0ySLJ46+ux1ytUojIQ3IpbOiyFO3ka9tMlx1iMrcfRwDt0u12H316ltKfJM+YcRPKBfJKr1osoxaRL9KxOKZhBvtXNL8/Ci8JwbGiDzbp2Lsflhk93DTvmybUMWWAOCnOFGabqMcCjYn9S3Gfz/34qzEjsQyHRjG90KQgnq7zGXIIECbDm3C8C+E26TChsRBf8q4d0K9azmCWfoS46cZimUCC/XoTNpz7Ga5omU01hyEGUEZykmpjQCntdGfb3iZRlRcmu/J7vUXOJOIxY5ia2fuc9RPoILEbALXFWeN8xA/Sc6QSrGz/Ye+dc+pmef3vihswVmMLc+D/mu686EcbW3MsWjAycaJjP6ARD9L/4iJynUYmTZ+cJ4X6rbCN52JYSjiRTrBbnBoaMy6fHyxmBCDi+tYhcM+00ohkJ5VNVW4lnvJAgWzVbi7pXwtyS/c7SPo7I0RuRqRiN5F2nwc7ZzOSN/nvOZfQdgU6T70B7nqT/lyboRhBEU4d5oz/ZoKcPZvChY/WiaGgr8achfLKP4xCdhWrR/9V3jLy30E8jIGVzdzrLA3rIa96myw6SLGvxELnrwE3T0HJAIoOwEUShQhKa/NJ4N6dUy139VfF8KaPwKbuLaBoef4ErWqRiFwGf0+1I7vJJHdA3TxXGOEH+oplb+MF1Dw7XTYlP1aD0cBuUg5CsTCi2a8snur10GVy1ZKSNEkA1qSdHZnq5MvR4Yvl3aCFq/c1hoFiAteDhLNkZsZC3GTxlnsFDJSC6KKVZv4UByBJ1YUNW5xqb/raDNEmMzeSRJXx9ki4Z5MBEojdKleYO2iv9BjSMjn4aBJVI6i5CgxT1BXti/R98EqPk0qxu6Txs/2j8ySWRbgYglWI8eNDM04ii+2+9CA1FX3fV1zaHM6FSoGVHSAkPav50DsuxztF6QkXcrFqypzWOuRhl/5XWK6Zb5lDNGbgPyljUhIc6R5AJIfJx9dq1ZfJuZC1n9O8boM50DyUnUBGLj/bC0yGwK9Nka8kSrwCx/VLG/yH9xXvEgC2y49jBdshB72CRHqs2HKH5HGGloHzdHWj0K4wk0jGIvQzdUoDsolZA9lTyFIviVvl1d4TpyCmrxV9NUSAGNqzXrknGHX4Ggcj3mk+h1rbcDutk+Qa//nXUf/511HFbQ=="
    }

    register_info = {
        "ttnet_sdk_version": "4.2.243.28-douyin",
        "auth_sdk_version": "4.6.2.4-bugfix",
        "code": end_code,
        "mix_mode": 1,
        "account_app_language": "zh",
        "language": "zh",
        "user_api_need_combine":1,
        "multi_login": 1,
        "sec_sdk_version": 67700992,
        "account_sdk_source": "app",
        "passport_support_flow": "real_name_check,choose_account,captcha,verify",
        "verify_sdk_version": "4.1.1.cn",
        "is_from_iesaccountsaas": 1,
        "email": email_code
        # "email": "6f6273327436757745343d3d68646c692b6666"
    }


    print(email_code)

    # 调用接口获取六神，并将六神更新至headers，更新业务接口params。注意，业务请求是POST时传data参数，GET不传。
    sixgoddata = core_sixgod(surl=url, params=params, devices={}, header=headers, log=False)
    sign_headers = sixgoddata["header"]
    sign_urls = sixgoddata["url"]
    # print(sign_urls)
    # print(sign_headers)

    # register_body = encrypt_tt(register_info)
    # print(register_info)
    # print(register_body)

    resp = requests.post(sign_urls, data=register_info, headers=sign_headers, proxies=proxy)
    print(resp.text)
    # resp_json = resp.json()
    # print(resp_json)


if __name__ == '__main__':
    # dev = {'server_time': 1750743863, 'device_id': 2675548328606650, 'install_id': 2675548328610746, 'new_user': 1,
    #        'device_id_str': '2675548328606650', 'install_id_str': '2675548328610746',
    #        'device_token': 'AAAVOIMFXSAU363RJXFTBEZFX2ASZPGQPQ65DIGC2WPM5CMUCCLWHSI2QND22KMYOY74A7U3FRCIVAJDET4LRCDUPNGC4OA5UYCAICAIHJCEMQWPKVG3T4PC37DYO',
    #        'dtrait_pk1': 'LS0tLS1CRUdJTiBSU0EgUFVCTElDIEtFWS0tLS0tCk1JSUJDZ0tDQVFFQXUvOHBiWGFrZjl3bklpOG50QUQrdEc5RXUzN2J5L2JDOUdDMDE5OW9nTkE1ZUpMZU9scWUKWW1iWk9RSWxnRTErWHZjeGFUdGc2Tys0Y2JPVHhQQzdPczIxdFlUZTB3aUMzUkw5eWdJQTkwOWlKcHVNWlBvdgpqVTJtek9abWdvYUlYVCsvdFBGalJXNnV5ODlkUVBjdEh6Zi9YejY2dGU5cVhqQWZzbmtBRVJQVmt2ZDR5eE4zCllyMGRHdUtOZHhCT3FhbkZya015c3ZvOXluVCtKa1UyS0tDRThJUlpKYnFGVjhab2VmaEFqd3pPKzFrSCs0OEwKOHlENmRLMSttYllXcUV6a0M0c1FYaHlNL25LWE1ZNktvTDFJdHk2TFlmNjhWQVQ1Y3VzMnhhK0c2Nng0VE9kbQpHeUw0bnZQbmE2akpVY2RXeUVVdzRYRWtjcmg0TVNMbkt3SURBUUFCCi0tLS0tRU5EIFJTQSBQVUJMSUMgS0VZLS0tLS0K',
    #        'dtrait_pk2': 'LS0tLS1CRUdJTiBSU0EgUFVCTElDIEtFWS0tLS0tCk1JSUJDZ0tDQVFFQXlFQkQ0MXQzcWpqL1NOaU5rT3BBbnNGdGZKZ0F5MGF5VTZCbEJ3RS9EZVZjNkdWV0xWUk4KWjdiMWRuRHVmQk5iUm1XQjlZeWVyYm1FOFFDM2lPOXp1NVFWd2x4SGV2ZEN0ZFFyeDZpQzF3QVRoaHFjdTNIYgprZ1dsazZ1Ylk5MXRvRFhNd0k2WGdmRUoyVEJsdHVSbklXRjR5RDVEaEc2c3lSSVNmNTRMWGY0WjgzbzlGcXNvCmlsNkV3cVZCbEU3dXlIY3dJOTA5WDg4Rlc3MXFLdmJMU040OGJlQ0EwbzFmZitqbmhRakNBTDZqbUR2dUhJeWEKUk1vYm1wRFVOLzQ3L3NHbDNzNDlFOEZFSEFXUmk5d1cyc2NZUDBJTkJXUlR5RlRHcG9GUGlqekJFUndnYzdrWQozVno3ZytSMXd2RkxUSEVITEtYUWFwTHpEMWR5Uk81YUt3SURBUUFCCi0tLS0tRU5EIFJTQSBQVUJMSUMgS0VZLS0tLS0K',
    #        'dtrait_pk1_version': 'a0', 'dtrait_pk2_version': 'b0', 'dtrait_version': 0, 'bind_dtrait': True,
    #        'iid': '2675548328610746', 'channel': 'xiaomi_1128_64', 'cdid': '4fe44377-5d85-43bf-8a22-b04251b942fe',
    #        'aid': '1128', 'app_name': 'amemv', 'version_name': '32.9.0', 'version_code': 320900,
    #        'device_type': '2103INT8LC', 'device_brand': 'Xiaomi', 'manifest_version_code': 320900,
    #        'update_version_code': 32909900, 'host_abi': 'arm64-v8a', 'brand': 'Xiaomi', 'model': '2103INT8LC',
    #        'resolution': '1260x2800', 'dpi': 229, 'build': 'XDG4.210307.768', 'rom': 'MIUI-V13.5.9.4.PAGGINXM',
    #        'rom_version': 'miui_V130_V13.5.9.4.PAGGINXM', 'device_platform': 'android', 'display_density': 'hdpi',
    #        'os': 'Android', 'os_version': '13', 'os_api': 33, 'mcc_mnc': '46005', 'carrier': '中国电信',
    #        'cpu_abi': 'arm64-v8a'}

    dev ={'os': 'Android', 'device_platform': 'android', 'device_type': 'ZTE 17', 'device_brand': 'ZTE', 'os_api': '29',
     'os_version': '10', 'openudid': 'c7002c4661063ba7', 'resolution': '1440*2392', 'dpi': '560',
     'cdid': 'c613a7f2-9d19-494a-9124-51429fa356e7', 'uuid': '7f0cdafd-3035-45c7-87f3-cb49f785ad0a',
     'clientudid': 'eefd7600-da37-447f-9bbe-3b44dac4e6b4', 'rom': 'EMUI-d8887c13f1025', 'rom_version': '8d',
     'mcc_mnc': '46007', 'host_abi': 'arm64-v8a', 'mac': '54:e3:38:c8:59:84',
     'sig_hash': '9390f046414c19a722c28ef9b5d809b5', 'release_build': '722ae99f-3ae6-4b56-a1d9-17a17ef7cddf',
     'req_id': '98db00c9-d740-41bc-8acb-53d3b03e942c', 'device_id': '1206613986551977', 'iid': '1206613986556073',
     'x_tt_dt': 'AAAWQBOHXQWXG3XERHNEFOXRRYHLGMLTMRBC4EQFWATXNOZTQFPTIRKFROS6W635UIPBQRLUJRCSUQQLOQJXOTI6PCI7HS2GAHSWDNVKT2SXLYGOBY2JACBTBHFUE',
     'aid': '1128', 'app_name': 'amemv', 'channel': 'douyin-ls-sm-xz-and-20', 'version_code': '320900',
     'version_name': '32.9.0', 'manifest_version_code': '320901', 'update_version_code': '32909900',
     'okhttp_version': '4.2.210.13-douyin', 'ttNet': 'TTNetVersion:9ac8d95c 2024-11-25 QuicVersion:3f326df4 2024-11-14',
     'ua': 'com.ss.android.ugc.aweme/320901 (Linux; U; Android 10; zh_CN; ZTE 17; Build/MMB29M; Cronet/TTNetVersion:9ac8d95c 2024-11-25 QuicVersion:3f326df4 2024-11-14)',
     'cookies': 'store-region=cn-js; store-region-src=did; install_id=1206613986556073; ttreq=1$adbb71698c738d36a9c510b3ebe5b91500993f3e'}

    code = '275498'
    mail = 'pmnf9xur@88vipmail.com'
    uuid_without_dashes ='5524c3aedd5c43aa8c4a17105a806465'

    email_signup(dev,mail,code,uuid_without_dashes)