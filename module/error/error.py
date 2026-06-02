class RetryException(Exception):
    """自定义异常，用于表示需要重试的情况"""
    def __init__(self, message="需要重试的操作"):
        self.message = message
        super().__init__(self.message)
