import json

import requests

from flurl3.core import core_sixgod

def api_slide_test(detail, lod_id, iid, did, proxies):
    data = {
        "uid": "dea889cd-d1e9-46ab-a2ac-71adcbc1156b",
        "service_name": "dy_android_slide_api",
        "aid": "1128",
        "detail": detail,
        "log_id": lod_id,
        "server_sdk_env": "{\"idc\":\"lf\",\"region\":\"CN\",\"server_type\":\"passport\"}",
        "proxies": proxies,
        "device_dict": {
            "did": did,
            "iid": iid
        }
    }
    url = 'http://180.97.215.147:9954/api/douyin/slide/android'
    header = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=data, timeout=20, headers=header)
    print(response.text)


install_id = "1290145667507628"
device_id = "2728334246030979"
proxies = {
    # 'http': 'http://d4955656459:7r59keie@171.41.131.246:20939',
    # 'https': 'http://d4955656459:7r59keie@171.41.131.246:20939'
}
url = "https://aggr5-normal-s12.amemv.com/passport/safe/query_account/"
params = {
    "passport-sdk-version": "60571",
    "request_from_account_sdk": "1",
    "is_from_ttaccountsdk": "1",
    "klink_egdi": "AALTZSVMzS6nbmKZNTlCACoSZbfufCiZJBMe0WnRg5iBpQ7emFB54Oc",
    "iid": install_id,
    "device_id": device_id,
    "ac": "wifi",
    "channel": "huoshan_fans_page_douyin",
    "aid": "1128",
    "app_name": "aweme",
    "version_code": "380900",
    "version_name": "38.9.0",
    "device_platform": "android",
    "os": "android",
    "ssmix": "a",
    "device_type": "AOSP on taimen",
    "device_brand": "Android",
    "language": "zh",
    "os_api": "30",
    "os_version": "11",
    "manifest_version_code": "380901",
    "resolution": "1440*2712",
    "dpi": "560",
    "update_version_code": "38909900",
    "_rticket": "1780240253909",
    "package": "com.ss.android.ugc.aweme",
    "first_launch_timestamp": "1779907858",
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
    "ts": "1780240290",
    "cdid": "2ba297c6-2411-48bb-9fc3-3c9d04edb4c8",
    "cronet_version": "5e677c20_2026-03-23",
    "ttnet_version": "4.2.278.4-douyin",
    "use_store_region_cookie": "1"
}
payload = {
  "is_vcd": "1",
  "reg_cookie_opt": "true",
  "ttnet_sdk_version": "4.2.278.8-douyin",
  "auth_sdk_version": "4.7.5",
  "enter_from": "recover",
  "hide_user_name_v3": "1",
  "mix_mode": "1",
  "area_code": "86",
  "account_app_language": "zh",
  "mobile": "2e3d33253432323d3d3d3d3c3c3c3d",
  "language": "zh",
  "query_type": "0",
  "multi_login": "1",
  "account_api_standard": "emo_douyin_account_recover",
  "scene": "find_account",
  "sec_sdk_version": "67764480",
  "account_sdk_source": "app",
  "passport_support_flow": "choose_account,captcha,real_name_check,verify",
  "verify_sdk_version": "4.1.3.cn"
}
headers = {
  'User-Agent': "com.ss.android.ugc.aweme/380901 (Linux; U; Android 11; zh_CN_#Hans; AOSP on taimen; Build/RP1A.200720.009; Cronet/TTNetVersion:e3d16265 2026-05-11 QuicVersion:afeca321 2026-04-27)",
  # 'Content-Type': "application/octet-stream",
  'x-tt-request-tag': "bdr-cnt=1;s=-1;p=0",
  'x-security-argus': "BridgeNetworkRequest/unknown aid/1128/huoshan_fans_page_douyin/Android/38.9.0/h5/213 https://api.amemv.com/ucenter_web/app/aweme/account_rebind_auth_verify",
  'contenttype': "application/x-www-form-urlencoded",
  # 'x-tt-passport-csrf-token': "01ff0f8438de198ae2c202b60e1ffc91",
  # 'x-tt-dt': "AAA6YGPFLZAOFVKA347OABDOAMX2LZLMVYWWSAE64DISCTXSXUOLVOFQOIYO3OQOOIFA72TO3UCLPO6DRSDYXQODE4XM3ILYZMRDY5GALQWJQ2E7FVNI6WVZJDVHBG6SK3SLYL7DOH6ERBSNUGY44OI",
  # 'activity_now_client': "1780240293418",
  # 'x-tt-device-dtrait': "a0_NdDdbaqXc/iwH4AV+WtO+PvaJh7LpAK3B66QwdrDEqianSsLdXCUOfcaPGUxUd/QS9NlbBYgaI0HhAEAzlUAmOwrFqAlDsPkdeZ+taXdtH+z/zQFEDq70TTTZWJqrbPebplItMHJsLfCZKwnrCKgIALEE/9ynI9KtAw/xMHXdco5oXpHZdvk9BUYMEC0iN/ym3uyBzDdpSPbivAc1V41XmT9TetcpMTORxl6cltpfWbTIB+ODe9kDZuY/m429+nwpsyoVrFmzEOxuL6rO4wwYaJOitjcwUK1qjyQ+H0P6j4s9x/Hm0aYGjtmbvIo1+oOpOK2+lfhSZ8mtr8oz1/+DA==",
  'bd-ticket-guard-display-os-version': "RP1A 200720.009 release-keys",
  'bd-ticket-guard-ree-public-key': "BESw/v0g6c3E7LP6vrPxKgmUjsOOTUhV9BdDexqSwUDFXsaowzboMa83bO11UkauzZrThxQEi72fHtGfvHmXm5M=",
  'bd-ticket-guard-version': "3",
  # 'x-tt-passport-verify-portrait-outer': "829ce87d-b795-49e2-9dcf-dc95cbe4ec87.find_account",
  # 'passport-sdk-settings': "x-tt-token,sec_user_id,device_transfer_s_0,device_transfer_ab_0",
  # 'passport-sdk-sign': "x-tt-token,sec_user_id",
  'bd-ticket-guard-tee-status': "1",
  'sdk-version': "2",
  'bd-ticket-guard-iteration-version': "2",
  # 'bd-ticket-guard-client-cert': "cHViLkJKcmFaNzd0MGc3d1hOSnV4RzNVaVR0d2s2YVVYZktHb2xiR3Q4Y1VrK3gvYUxtSHkrOVlEcGMySzJaeDMwYU51K0loa3dRSGxJT21vd1ZxeE9PLzJ2VT0=",
  # 'bd-ticket-guard-static-sign': "MEUCIQC0tLRiPkA1ge0V7Mwnyxn2uG7U506ysAh/DTHpo20FuAIgfDVSS0kf1fWiqABgZJHrzDQeDuwX/+2Y4mpsdqLsr3c=",
  # 'bd-ticket-guard-server-cert-sn': "533240336124694022040808462028007165443034493949",
  # 'x-tt-passport-trace-id': "find_account_20e1cf0de00747f5a9626a4528478651",
  # 'bd-ticket-guard-sec-ts': "#f7xqQJXp6YM3USgf3ZGQ6Ou8OnTTVTOnkhYmrvi35NE2GY6/uLe1qI85n6pg",
  'passport-sdk-version': "60571",
  'x-ss-req-ticket': "1780240253926",
  'x-vc-bdturing-sdk-version': "4.1.3.cn",
  'content-type': "application/x-www-form-urlencoded; charset=UTF-8",
  'x-ss-stub': "1FB719D47D4070285F442B93B5FE4561",
  # 'x-bd-content-encoding': "zstd",
  'x-tt-bdturing-retry': "1",
  'x-tt-ttnet-origin-host': "api5-normal-lq.amemv.com",
  'x-ss-dp': "1128",
  # 'x-tt-trace-id': "01-7e96f65b0d9b167d1902e83098ba0468-7e96f65b0d9b167d-00",
  # 'x-perseus': "LpLLLlNWN65jjiF/nzZvl9xvpt6shTLg54vRKUcHYvin6LwKnaDHWhybts/lRdYp1ZxxerWygBqXlqxheY8hgIjLy9v2RhWqQzxtwcwfhTqIRR8z3xdH2eXzDlPhURySbx53cL0mQEZvbypAufYh2SQBt3m0EJ8QlUw+cdIP5C11G4kFt4/PXwNzHMSgaAoIJ9rgeOw6QP6Lb6/x7br7oXQqJARxCDTYxWSJZ8nDirddSQRAWxvqsTcSqeOeF+Yy7evG1aPAsai8Ly5e0WLT6hj2YzyM+2iZDAzGYS4O7EulxffNJYja4y5uEDdvGzFWqTz+KhCTvnwgzF7kCBmS3n+PshRovmDRxVhDC3fvsGu3SBL6ai5O7u5XpbnjklLeRKbU4BbVNyI16dXd2Q7zMwpKrW/50FJOHARI3wh8dX6xzYtKLKcwn4JQDaAmbo9JJdrgvFoTSeQlmQVd7GwG9oEJQbedOGttcu9jPTU9+xKEsGRtmR1YZ/Iys2yNjZ71zU+gNx7mGc84UiAYv3NkDlto5nngCqJeNSWricbG/jaHqUmdmPCHIKYF8j8VkfX0sWuIVdTwEqIY+/+Wzx3cTmJNTUU2tJcb8NrFm8dPoEXilOOHfgqWqIQ6Zj7AkVKZ0E+2uyMPQkCHlHOS6F7f4AgxobDFoe7gAA9mTFmuSY9zYOkT2sgECuiP1CrNg3BYKT05PzCIorGcPMfv33ChQBF/YZFRjpZ/t8/NycHhnHj9e4IDEOMZ49wh52ed8NSgM4VCLRkLImgv7OqJQkd0iKb1/jqE9HrQoT4t/sH6/07QvYWSPVbUwomZpQws7MOQVh/9klWpmoR5D3kZSkTo7NPGfYwye7MeX0b5VaMk4nQjPGEQeuSCIQgkAsy7+0l/gxD9PeludD==",
  # 'x-medusa': "ck8cah7VN0A31LP79IUeALd5uJRwYwANJouELpi/19t7CJT+yDVfNrV1AUIZmCENNrlDloqyPnqcraad1T9zOeB03P8O1BACpOxUmpByPu7Wv625zhDicBs0vzDD5caLN/M5885DEvQ1drYMAS1HdBkdKg6LY+eZTJwJAfAtzixvgOAnt87Ulcud6oq2Lo8D3y81lPDGSCxFaXlQORO+gjyrOc+aTGYBgbRAGAFrx05rS4bpwFFEFxX8QxB2/8PakxvKpetdRxj7Qlg/mTMfzPW2MFYJbn3chZWq2up1V5kUtwff9SLlj007rry4y6cRuQZ83acTivpR+dajPy5izWh1A/h+Mf/4pzH/+KfrIg==",
  # 'x-argus': "dU8cag==",
  # 'x-gorgon': "8404c0c200004d604c291c751ef5e77fd68e594e2341c7e9df6b",
  # 'x-helios': "nI0BKZn4qH8iEd0Dim4CCA3qENyUJwr7JzVuAdjHlMZDLPue",
  # 'x-ladon': "et2C+w==",
  # 'x-khronos': "1780240245",
  'Cookie': f"store-region=cn-fj; store-region-src=did; install_id={install_id}; ttreq=1$9380e7ed80dc051525b7e3479b6c1959535ad289; passport_csrf_token=01ff0f8438de198ae2c202b60e1ffc91; passport_csrf_token_default=01ff0f8438de198ae2c202b60e1ffc91; odin_tt=204d6bcdabd115d2eba759df0c519c1cdcd44c12c2f726b371a36ba196b86cb69b7c4ee053979b567563edba4527a1ed0fa2d018c21d4ad349087c01d629e4e88f4a1079230d4713d2f8ba28060db270"
}
sixgoddata = core_sixgod(surl=url, params=params, data=payload, devices={}, header=headers, log=False)
# print(sixgoddata)
sign_headers = sixgoddata["header"]
sign_urls = sixgoddata["url"]

response = requests.post(sign_urls, data=payload, headers=sign_headers,proxies=proxies)
print(response.text)

if response.json()['message'] == 'error':
    verify_center_decision_conf = json.loads(response.json()['data']['verify_center_decision_conf'])


    api_slide_test(verify_center_decision_conf['detail'],verify_center_decision_conf['log_id'],install_id,device_id, proxies )

response = requests.post(sign_urls, data=payload, headers=sign_headers,proxies=proxies)
print(response.text)



