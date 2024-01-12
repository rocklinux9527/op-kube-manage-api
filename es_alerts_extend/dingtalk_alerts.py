from elastalert.alerts import Alerter
import time
import requests
import json
import hmac
import hashlib
import base64
import urllib.parse


# 定义一个名为DingTalkAlerter的类，它是Alerter类的子类
class DingTalkAlerter(Alerter):
    # 定义类属性required_options，它是一个字典，包含一个键'dingtalk'
    required_options = {'dingtalk'}
    # 构造方法，初始化DingTalkAlerter对象
    def __init__(self, rule):
        # 调用父类Alerter的构造方法，传入rule参数，完成通用的初始化工作.
        super(DingTalkAlerter, self).__init__(rule)
        # 从rule参数中获取dingtalk字典中的app_id、app_secret等属性，并赋值给对应的实例属性
        self.webhook_url = self.rule["dingtalk"]["webhook_url"]
        self.secret = self.rule["dingtalk"].get("secret")
        self.dingtalk_signature = self.get_dingtalk_signature(self.secret)
    print(required_options)

    def get_dingtalk_signature(self,secret):
        timestamp = str(round(time.time() * 1000))
        secret_enc = secret.encode('utf-8')
        string_to_sign = '{}\n{}'.format(timestamp, secret)
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return f"{self.webhook_url}&timestamp={timestamp}&sign={sign}"

    def alert(self, matches):
        print("告警信息")
        print(matches)
        try:
            dingtalk = DingTalkMessage(self.dingtalk_signature)
            dingtalk.markdown(title="nginx 403状态检查",text=DingTalkMessage.index_matches_format(matches),is_at_all=True)
        except Exception as e:
            raise Exception("Error request to dingtalk error: {}\n{}".format(str(e)))

    def get_info(self):
        return {
            "type": "dingtalk",
            "timestamp": time.time()
        }


class DingTalkMessage:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
        self.headers = {"Content-Type": "application/json;charset=utf-8"}

    def _send_message(self, data):
        try:
            response = requests.post(url=self.webhook_url, data=json.dumps(data), headers=self.headers)
            response.raise_for_status()
            result = response.json()
            if result.get("errcode") != 0:
                print(f"发送消息失败：{result.get('errmsg')}")
        except Exception as e:
            print(f"发送消息失败：{e}")

    def text(self, content, at_mobiles=None, is_at_all=False):
        data = {"msgtype": "text", "text": {"content": content}, "at": {}}
        if is_at_all:
            data["at"]["isAtAll"] = True
        elif at_mobiles:
            data["at"]["atMobiles"] = at_mobiles
        self._send_message(data)

    def link(self, title, text, message_url, pic_url=None):
        data = {"msgtype": "link", "link": {"title": title, "text": text, "messageUrl": message_url}}
        if pic_url:
            data["link"]["picUrl"] = pic_url
        self._send_message(data)

    def markdown(self, title, text, at_mobiles=None, is_at_all=False):
        data = {"msgtype": "markdown", "markdown": {"title": title, "text": text}, "at": {}}
        if is_at_all:
            data["at"]["isAtAll"] = True
        elif at_mobiles:
            data["at"]["atMobiles"] = at_mobiles
        self._send_message(data)

    @staticmethod
    def index_matches_format(matches):
        if isinstance(matches,list):
           result_list = [{'domain': item['domain'],'response': item['response'],'remote_addr': item['remote_addr'],'scheme': item['scheme'],'request_uri': item['request_uri']} for item in matches]
           for item in result_list:
                markdown_message =  DingTalkMessage.generate_markdown_message(item)
                return markdown_message
        else:
           print("data is not list")

    @staticmethod
    def generate_markdown_message(item):
        current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        message = """
        [域名403告警] \n\
        检测时间：{current_time} \n\
        检测对象：nginx-access-log \n\
        访问协议：{scheme} \n\
        访问path: {request_url} \n\
        访问IP：  {remote_addr} \n\
        检查域名：{domain} \n\
        域名状态:  {status} \n\
        检查结果: Success \n\
        """.format(current_time=current_time,domain=item["domain"],scheme=item['scheme'],status=item['response'],remote_addr=item['remote_addr'],request_url=item['request_uri'])
        return message

    def action_card(self, title, text, btns, btn_orientation="1"):
        data = {"msgtype": "actionCard", "actionCard": {"title": title, "text": text, "btnOrientation": btn_orientation, "btns": btns}}
        self._send_message(data)

    def feed_card(self, links):
        data = {"msgtype": "feedCard", "feedCard": {"links": links}}
        self._send_message(data)