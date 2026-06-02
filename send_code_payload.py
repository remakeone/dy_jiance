from flurl.core import core_sixgod

import uuid
import requests


def toke_phone_num(phone_num):
    bytes_phone_number_data = phone_num.encode("utf-8")
    xor_bytes = bytes([byte ^ 5 for byte in bytes_phone_number_data])
    # 逐字节转换为十六进制字符串并拼接
    hex_string = ''.join(format(byte, '02x') for byte in xor_bytes)
    return hex_string

def send_email_code(dev, mail,uuid_without_dashes,proxy=None):

    email_code = toke_phone_num(mail)
    # 拼接发送请求的 url
    url = "https://api3-normal-c-lq.amemv.com/passport/email/send_code/"

    params = {
        "passport-sdk-version": "601431",
        "request_from_account_sdk": "1",
        "is_from_ttaccountsdk": "1",
        "iid": dev["iid"],
        "device_id": dev["device_id"],
        "ac": "wifi",
        "channel": "googlePlay",
        "aid": "1128",
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
        "_rticket": "1770624652624",
        "package": "com.ss.android.ugc.aweme.mobile",
        # "package": "com.ss.android.ugc.livepro",
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
        "ts": "1770624650",
        "cdid": dev["cdid"],
        "md": "0",
        "cronet_version": "b9c3e521_2025-09-09",
        "ttnet_version": "4.2.243.16-douyin",
        "use_store_region_cookie": "1"
    }

    headers = {
        # ":method": "POST",
        # ":authority": "api3-normal-c-lq.amemv.com",
        # ":path": "/passport/email/send_code/?passport-sdk-version=601431&request_from_account_sdk=1&is_from_ttaccountsdk=1&iid=7604774384485746213&device_id=2051038435907593&ac=wifi&channel=googlePlay&aid=1128&app_name=aweme&version_code=370100&version_name=37.1.0&device_platform=android&os=android&ssmix=a&device_type=OPPO+A4&device_brand=OPPO&language=zh&os_api=33&os_version=13&manifest_version_code=370100&resolution=1080*2132&dpi=450&update_version_code=37109900&_rticket=1770624652624&package=com.ss.android.ugc.aweme.mobile&first_launch_timestamp=1766049783&last_deeplink_update_version_code=0&cpu_support64=true&host_abi=arm64-v8a&is_guest_mode=0&app_type=normal&minor_status=0&appTheme=light&is_preinstall=0&need_personal_recommend=1&is_android_pad=0&is_android_fold=0&ts=1770624650&cdid=c85ccce4-d2fa-49b4-8ebb-08d3ecaa5392&md=0&cronet_version=b9c3e521_2025-09-09&ttnet_version=4.2.243.16-douyin&use_store_region_cookie=1",
        # ":scheme": "https",
        # "content-length": "486",
        # "cookie": "ttreq=1$5d2ed25398d796fc11961d1bf9b034f0a256823f",
        # "x-tt-passport-csrf-token": "b224627dccef94606c9aeac84d0cb414",
        # "x-tt-dt": "AAA27EDINIESDZL6JZAWV47GMZYVNPJRIRWHL3TXUOOKAFN7KH52J5M7MHH4AYSMQNXMFJFOLWZXGPQGSKQJA5U6ZZTHUSLPMWVEJGO4J4XIKSMO73OJUAKWDVILI",
        "activity_now_client": "1770624651494",
        "x-ss-req-ticket": "1770624652626",
        "bd-ticket-guard-tee-status": "1",
        "bd-ticket-guard-display-os-version": "TQ3A.230705.001",
        "sdk-version": "2",
        # "bd-ticket-guard-ree-public-key": "BGlj0nh7FkMzE3yj+SoDtJL5je3nDX82ICsaEaybgIoRxoBvCiVXV3gXPy6qaljlJboSMYKo3bxOfwtoxZJEDOg=",
        "bd-ticket-guard-version": "3",
        "bd-ticket-guard-iteration-version": "2",
        # "bd-ticket-guard-client-cert": "cHViLkJHb2U1bWkwUC9IazJZQ2xoeHlzbnNmWXJmSlhMTWtwMC9HNi9wZHQyQ0swVktrZm5rZGFWTytJM1M1SVc0VjdaVlVVcFpZUU94alVjQWxUSTJ3d0VGVT0=",
        # "bd-ticket-guard-server-cert-sn": "533240336124694022040808462028007165443034493949",
        # "x-tt-passport-trace-id": "login_06ea97c18dda4b3daae03d7860146877",
        "x-tt-passport-trace-id": f"login_{uuid_without_dashes}",
        "passport-sdk-settings": "x-tt-token,sec_user_id",
        "passport-sdk-sign": "x-tt-token,sec_user_id",
        "passport-sdk-version": "601431",
        "x-vc-bdturing-sdk-version": "4.1.1.cn",
        # "x-tt-cipher-version": "1.0.0",
        # "x-tt-encrypt-info": "1",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        # "Content-Type": "application/octet-stream",
        # "x-ss-stub": "56229ED539A3C5729C64A58A75D1A9BD",
        "x-tt-request-tag": "s=0;p=0",
        "x-ss-dp": "1128",
        # "x-tt-trace-id": "00-417416f70d749689964980967fe50468-417416f70d749689-01",
        # "user-agent": "com.ss.android.ugc.aweme.mobile/370100 (Linux; U; Android 13; zh_CN; OPPO A4; Build/TQ3A.230705.001; Cronet/TTNetVersion:6f1e308d 2025-12-08 QuicVersion:21ac1950 2025-11-18)",
        "User-agent": "com.ss.android.ugc.aweme.mobile/370100 (Linux; U; Android 13; zh_CN; OPPO A4; Build/TQ3A.230705.001; Cronet/TTNetVersion:6f1e308d 2025-12-08 QuicVersion:21ac1950 2025-11-18)",
        # "accept-encoding": "gzip, deflate, br"
        # "x-argus": "jJaJaQ==",
        # "x-gorgon": "840410ac0000ed532cde52035f4bfe0aa3dfcb730a6b02852973",
        # "x-helios": "tdK0LY1LtB64HMIZz3ECodfcAomQyGv9iUcmOzNX8iEttXpL",
        # "x-khronos": "1770624652",
        # "x-ladon": "9bIRew==",
        # "x-medusa": "iZaJaaHdxqPF44QqsyMnRa77RT85PQABZ3UU3P1Cgd0CGPVefAXpUjPVp8/4TTQrRBXZoEnzeB0kms60eRJ01RqcO6Ogtro02X9+xbWacTQLHKRYl3sdKGOUwlTBokzMCK7HmhF/QUQra6Tt8yaWsqdaxJJxv4esE+dGf0e6j+P6Vx2SCvH/cgso4wz4H74dZmAGhj0EhV/bBKYeJ8biL01QmLMJU+0yS4qNp5D2g2SPZ/uUn+TS4h7ab5GWwXp4LD5KPfJO19B1RPRf5gabMsFOyllOKBOqZSuqG7/ygPn/kavfsgQFF50WcaLVeEhsid6Apk8gFV6m8sUA3jqV76f09bu6nQi01aLQOlwUOUjhNq6IvoxpZDniwJLmyk9EB2yTRRSlVkMlaZsUOOcAPPv38zlvbrKXzSY7ald0mU0owUy3epsJL1dKQy02oRNCRIIDOHV9A9+6P3REJUI8kIX0dLs8hv64CtqT8B+OvkcpI/0uvhmaSiI3rQgi8cMb3dCKxT2vnR5wpVeplLF/5lQlIvFI6z2lSZialbkoQImi+SfwixRZKZNOn7CZbqRiWUedBB5pkKK/KEB8HWEIuJyExP+MSVDKwMaXLXX99T32eJO1BQjfwSWrUjFsbax5K2WWaQH69bGbQUPzYVRAgrEnFr9sVkj4UoZ8czVzkJbUk1A5ro42RDFCfu+7n2nqHokmoPxVni21xcz1dGLHGTm7ZU+7QDdwZNkSuGVfkUGXnWjpdWX3FWfeuegd9v1zfNsLelLRNedI6BnZz8GSX+nYDWIsntC0XeMuYoiRYVkUwBnCfAHWBQLMJt/lROOwx0s7jnNS0HJUiWb7xspg+y67JeT4XEeQsSyOh1YKlFS37lOtdCBKvCUUU5FTpOwN9UcsD5dgCnvLMiTZ02hnFB+OFCYa2bkLCXD4JV7CHCeWaL8Mvfa1iCzUt3EeADgA6pBfAtWntQlCMeUCH/AxSNHLQLjrWd2E1hgy63axiVw5O/X1XPrE/TAXx1WnoGe8kF3QC4flqZxxra2c7iQNcpllpBD1aGvs8x6v8PufEobNhAedSeIjrwbrH6joCT9CZGh9IqdpUnpcJK8n5STBfpuFXObKFDd6KxpkuLpDB0+6yHf5Rd9kWMHTXvtLUXsvOCsAyCYBRH7iMJ8uR/iQ+5CtyxKpqxa94tI58mO+uszgtn9kFkqjguBk8TEl3Xt22qXCQm82//jHNv/4x+cp"
    }

    cookie = {
        "passport_csrf_token": "b224627dccef94606c9aeac84d0cb414",
        "passport_csrf_token_default": "b224627dccef94606c9aeac84d0cb414",
        "store-region": "cn-hk",
        "store-region-src": "did",
        "odin_tt": "f364e36cd7250bd08e98b2eca5e1060f4ca2e3400241b303f9ba65a0a9ef1d0150686574b89200e8aa4614474ec165670089ed8b9e98e20023322362866563c248b5d38750765db8991a678d31775e0d",
        "install_id": "7604774384485746213",
        "ttreq": "1$5d2ed25398d796fc11961d1bf9b034f0a256823f"
    }

    register_info = {
        "is_vcd": "0",
        "reg_cookie_opt": "true",
        "ttnet_sdk_version": "4.2.243.28-douyin",
        "auth_sdk_version": "4.6.2.4-bugfix",
        "mix_mode": 1,
        "account_app_language": "zh",
        "language": "zh",
        "multi_login": 1,
        "type": 3433,
        # "sec_sdk_version": 67700736,
        "sec_sdk_version": 67700992,
        "account_sdk_source": "app",
        "passport_support_flow": "real_name_check,choose_account,captcha,verify",
        "verify_sdk_version": "4.1.1.cn",
        "is_from_iesaccountsaas": 1,
        "email": email_code
        # "email": "6f6273327436757745343d3d68646c692b6666"
    }

    # 调用接口获取六神，并将六神更新至headers，更新业务接口params。注意，业务请求是POST时传data参数，GET不传。
    sixgoddata = core_sixgod(surl=url, params=params,data=register_info, devices={}, header=headers, log=False)
    sign_headers = sixgoddata["header"]
    sign_urls = sixgoddata["url"]
    print(sign_urls)
    print(sign_headers)

    # 请求体加密过程
    # register_body = encrypt_tt(register_info)
    print(register_info)

    resp = requests.post(sign_urls, data=register_info, headers=sign_headers,proxies=proxy)
    # resp = requests.post(sign_urls, data=register_info, headers=headers)
    print(resp.text)
    print(resp)

    return resp


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

    dev = {'os': 'Android', 'device_platform': 'android', 'device_type': 'ZTE 17', 'device_brand': 'ZTE',
           'os_api': '29',
           'os_version': '10', 'openudid': 'c7002c4661063ba7', 'resolution': '1440*2392', 'dpi': '560',
           'cdid': 'c613a7f2-9d19-494a-9124-51429fa356e7', 'uuid': '7f0cdafd-3035-45c7-87f3-cb49f785ad0a',
           'clientudid': 'eefd7600-da37-447f-9bbe-3b44dac4e6b4', 'rom': 'EMUI-d8887c13f1025', 'rom_version': '8d',
           'mcc_mnc': '46007', 'host_abi': 'arm64-v8a', 'mac': '54:e3:38:c8:59:84',
           'sig_hash': '9390f046414c19a722c28ef9b5d809b5', 'release_build': '722ae99f-3ae6-4b56-a1d9-17a17ef7cddf',
           'req_id': '98db00c9-d740-41bc-8acb-53d3b03e942c', 'device_id': '3370434010877385', 'iid': '1364924804650564',
           'x_tt_dt': 'AAAWQBOHXQWXG3XERHNEFOXRRYHLGMLTMRBC4EQFWATXNOZTQFPTIRKFROS6W635UIPBQRLUJRCSUQQLOQJXOTI6PCI7HS2GAHSWDNVKT2SXLYGOBY2JACBTBHFUE',
           'aid': '1128', 'app_name': 'amemv', 'channel': 'douyin-ls-sm-xz-and-20', 'version_code': '320900',
           'version_name': '32.9.0', 'manifest_version_code': '320901', 'update_version_code': '32909900',
           'okhttp_version': '4.2.210.13-douyin',
           'ttNet': 'TTNetVersion:9ac8d95c 2024-11-25 QuicVersion:3f326df4 2024-11-14',
           'ua': 'com.ss.android.ugc.aweme/320901 (Linux; U; Android 10; zh_CN; ZTE 17; Build/MMB29M; Cronet/TTNetVersion:9ac8d95c 2024-11-25 QuicVersion:3f326df4 2024-11-14)',
           'cookies': 'store-region=cn-js; store-region-src=did; install_id=1364924804650564; ttreq=1$adbb71698c738d36a9c510b3ebe5b91500993f3e'}


    mail = 'pmnf9xur@88vipmail.com'
    # 生成一个新的 UUID
    original_uuid = uuid.uuid4()

    # 将 UUID 转为字符串并去除其中的横杠
    uuid_without_dashes = str(original_uuid).replace('-', '')

    # # 输出结果
    # print("原始 UUID:", original_uuid)
    print("去除横杠后的 UUID:", uuid_without_dashes)
    send_email_code(dev,mail,uuid_without_dashes)

