from module.device_regist.flurl.utils import *

def generate_url_params(dev_info, extra={}):
    rticket = round(time.time() * 1000)
    first_ts = round(time.time())
    ts = round(time.time())
    url_params = {
        'tt_data': 'a',
        'ac': 'wifi',
        'channel': dev_info['app']['channel'],
        'aid': '1128',
        'app_name': 'aweme',
        'version_code': dev_info['app']['version_code'],
        'version_name': dev_info['app']['version_name'],
        'device_platform': 'android',
        'os': 'android',
        'ssmix': 'a',
        'device_type': dev_info['device']['device_type'],
        'device_brand': dev_info['device']['device_brand'],
        'language': 'zh',
        'os_api': dev_info['device']['os_api'],
        'os_version': dev_info['device']['os_version'],
        'openudid': dev_info['device']['openudid'],
        'manifest_version_code': dev_info['app']['manifest_version_code'],
        'resolution': dev_info['device']['resolution'],
        'dpi': dev_info['device']['dpi'],
        'update_version_code': dev_info['app']['update_version_code'],
        '_rticket': rticket,
        'package': 'com.ss.android.ugc.aweme',
        'first_launch_timestamp': first_ts,
        'last_deeplink_update_version_code': '0',
        'cpu_support64': 'true',
        'host_abi': 'arm64-v8a',
        'is_guest_mode': '0',
        'app_type': 'normal',
        'minor_status': '0',
        'appTheme': 'light',
        'is_preinstall': '0',
        'need_personal_recommend': '1',
        'is_android_pad': '0',
        'is_android_fold': '0',
        'ts': ts,
        'cdid': dev_info['device']['cdid'],
        'md': '0',
        'okhttp_version': dev_info['app']['okhttp_version'],
        'use_store_region_cookie': '1'
    }
    merged_params = url_params | extra
    return merged_params

def generate_url_common_params(dev_info, extra={}):
    url_params = generate_url_params(dev_info,extra)
    return urllib.parse.urlencode(url_params)
