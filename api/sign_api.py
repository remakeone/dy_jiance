import traceback

from flask import Flask, request, jsonify
from module.six_god.Encrypt import Encrypt

app = Flask(__name__)

@app.route('/sign_ios', methods=['POST'])
def sign_ios_endpoint():
    try:
        # 获取请求参数
        params = request.get_json()
        print(params)
        required_fields = ['url', 'data', 'device_info']
        if not all(field in params for field in required_fields):
            return jsonify({'error': 'Missing required parameters'}), 400

        # 初始化加密对象
        encrypt = Encrypt(params['device_info'])
        if 'devicetoken' not in params['device_info']:
            params['device_info']['devicetoken'] = ""
        # 调用签名方法
        result = encrypt.sign_ios(
            url=params['url'],
            data=params.get("data", None),
            devices=params['device_info'],
            lanusk=params.get('lanusk', ""),
            prl=params.get('prl', 'ios').lower()
        )

        return jsonify(result)

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
