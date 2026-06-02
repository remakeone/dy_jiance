from PJYSDK import PJYSDK
import os
import time
import tkinter as tk
from tkinter import messagebox
from generate_device_id import generate_device_id

# 初始化 app_key 和 app_secret 在开发者后台新建软件获取
pjysdk = None # type: PJYSDK

# 创建一个隐藏的Tk根窗口用于显示消息框
root = tk.Tk()
root.withdraw()  # 隐藏主窗口

# 心跳失败回调
def on_heartbeat_failed(hret):
    # print(hret.message)
    messagebox.showerror("错误", hret.message)
    if hret.code == 10214:
        os._exit(1)  # 退出脚本
    # print("心跳失败，尝试重登...")
    messagebox.showwarning("警告", "心跳失败，尝试重登...")
    login_ret = pjysdk.card_login()
    if login_ret.code == 0:
        # print("重登成功")
        messagebox.showinfo("提示", "重登成功")
    else:
        # print(login_ret.message)  # 重登失败
        messagebox.showerror("错误", f"重登失败: {login_ret.message}")
        os._exit(1)  # 退出脚本


def init_card_password(card_password,app_key,app_secret, debug=False):
    global pjysdk
    pjysdk = PJYSDK(app_key=app_key, app_secret=app_secret)
    pjysdk.debug = debug
    pjysdk._heartbeat_gap = 5*60
    pjysdk.on_heartbeat_failed = on_heartbeat_failed  # 设置心跳失败回调函数
    device_id = generate_device_id(True)
    pjysdk.set_device_id(device_id)  # 设置设备唯一ID
    pjysdk.set_card(card_password)  # 设置卡密

    ret = pjysdk.card_login()  # 卡密登录
    if ret.get('code') != 0:  # 登录失败
        # print(ret.message)
        messagebox.showerror("登录失败", f"卡密：{card_password}\n错误信息：{ret.message}")
        time.sleep(0.2)
        # input(f'登录失败，卡密：{card_password}，请检查卡密是否正确，点击回车退出')
        messagebox.showinfo("提示", "请检查卡密是否正确")
        os._exit(1)  # 退出脚本


def read_card_password(path='card_password.txt'):
    """
    从文件中读取卡密
    """
    if not os.path.exists(path):
        # print(f'文件不存在：{path}')
        with open(path, 'w') as f:
            f.write('')
        messagebox.showerror("错误", f"卡密为空，请将卡密写入文件{path}")
        os._exit(1)  # 退出脚本

    with open(path, 'r') as f:
        card_password = f.read().strip()
        if not card_password:
            # print(f'文件{path}为空')
            messagebox.showwarning("警告", f"文件{path}为空")
            time.sleep(0.2)
            # input(f'请在文件{path}中输入卡密。点击回车退出')
            messagebox.showinfo("提示", f"请在文件{path}中输入卡密。")
            os._exit(1)  # 退出脚本

    return card_password


if __name__ == '__main__':
    pass