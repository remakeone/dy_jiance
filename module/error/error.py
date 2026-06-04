class RetryException(Exception):
    """自定义异常，用于表示需要重试的情况"""
    def __init__(self, message="需要重试的操作"):
        self.message = message
        super().__init__(self.message)


class SystemBusyException(RetryException):
    """系统繁忙，需更换设备后重试同一任务"""


class ProxyInvalidException(Exception):
    """提取式代理失效（通常由网络异常触发），需重新拉取代理"""


class CaptchaFailedException(Exception):
    """滑块验证失败或重试耗尽"""
