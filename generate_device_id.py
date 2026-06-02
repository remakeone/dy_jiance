import hashlib
import platform
import subprocess
import uuid
import re


def get_device_info():
    """收集设备硬件信息"""
    info = {}

    # 获取操作系统信息
    info['os'] = platform.platform()

    # 获取MAC地址
    try:
        mac = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
        info['mac'] = mac
    except:
        info['mac'] = "unknown_mac"

    # 获取CPU信息
    try:
        if platform.system() == "Windows":
            info['cpu'] = platform.processor()
        elif platform.system() == "Darwin":
            info['cpu'] = subprocess.check_output(['sysctl', '-n', 'machdep.cpu.brand_string']).strip().decode()
        elif platform.system() == "Linux":
            info['cpu'] = \
            subprocess.check_output(['cat', '/proc/cpuinfo']).decode().split('model name')[1].split('\n')[0].split(':')[
                1].strip()
        else:
            info['cpu'] = platform.processor()
    except:
        info['cpu'] = "unknown_cpu"

    # 获取硬盘序列号
    try:
        if platform.system() == "Windows":
            result = subprocess.check_output(['wmic', 'diskdrive', 'get', 'serialnumber']).decode().split('\n')[
                1].strip()
            info['disk'] = result if result else "unknown_disk"
        elif platform.system() == "Linux":
            info['disk'] = \
            subprocess.check_output(['hdparm', '-i', '/dev/sda']).decode().split('SerialNo=')[1].split('\n')[0].strip()
        elif platform.system() == "Darwin":
            info['disk'] = \
            subprocess.check_output(['diskutil', 'info', '/']).decode().split('Volume UUID:')[1].split('\n')[0].strip()
        else:
            info['disk'] = "unknown_disk"
    except:
        info['disk'] = "unknown_disk"

    return info


def generate_device_id(need_log=False):
    """生成32位设备ID"""
    info = get_device_info()
    print("收集的设备信息:")
    if need_log:
        for k, v in info.items():
            print(f"{k.upper()}: {v}")
    combined = f"{info['os']}|{info['mac']}|{info['cpu']}|{info['disk']}"
    return hashlib.md5(combined.encode()).hexdigest()


if __name__ == "__main__":
    device_id = generate_device_id(True)

    print("\n生成的设备ID:")
    print(device_id)