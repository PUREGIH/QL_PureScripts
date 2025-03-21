# -*- coding=UTF-8 -*-
# @Project          QL_TimingScript
# @fileName         浓五的酒馆.py
# @author           Echo
# @EditTime         2025/3/21
# const $ = new Env('浓五的酒馆');
"""
开启抓包进入‘浓五的酒馆’小程序，抓取authorization，不要带Bearer
变量格式：
    - nwjg_token，多个账号用@隔开
    - wxid_nwjg，多个用#隔开
    - wxcenter， 你的 code server (http://localhost:5679)

"""
import os
import re

import httpx

from fn_print import fn_print

from get_env import get_env

nwjg_tokens = get_env("nwjg_token", "@")

wxcenter = os.environ.get('wxcenter')

wxid_nwjg = get_env("wxid_nwjg", "#")

app_id = "wxed3cf95a14b58a26"


class Nwjg:
    def __init__(self, token=None, wxid=None):

        self.user = None
        self.client = httpx.Client(
            verify=False,
            timeout=60
        )
        self.token = token
        self.promotionID = None
        self.__code = None
        self.nwjg_wxid = wxid

    @property
    def base_headers(self):
        return {
            'Content-Type': 'application/json',
            'Host': 'stdcrm.dtmiller.com',
            'User-Agent': ('Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) '
                           'AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 '
                           'MicroMessenger/8.0.56(0x1800383a) NetType/4G Language/zh_CN')
        }

    @property
    def headers(self):
        headers = self.base_headers.copy()
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        return headers

    def get_wxcode(self) -> None:
        headers = {
            'Content-Type': 'application/json'
        }
        try:
            response = self.client.post(
                url=f"{wxcenter}/api/wxapp/JSLogin",
                headers=headers,
                json={"wxid": self.nwjg_wxid, "appid": app_id}
            )

            response.raise_for_status()
            response_data = response.json()

            if response_data.get('Success') is True:
                code = response_data.get('Data', {}).get('code')
                if code:
                    fn_print(f"✅ 获取 code 成功: {code}")
                    self.__code = code
                    self.get_token()

        except Exception as e:
            fn_print(f"❌ 获取 code 失败: {e}")

    # def get_sign_promotion_id(self) -> None:
    #
    #     try:
    #         response = self.client.post(
    #             url="https://stdcrm.dtmiller.com/scrm-promotion-service/mini/module/config/list",
    #             headers=self.headers
    #         ).json()
    #
    #         for module in response.get("data", []):
    #             for detail in module.get("detailList", []):
    #                 detail_json_str = detail.get("detailJson", "{}")
    #                 detail_json = json.loads(detail_json_str)
    #
    #                 jump_data = detail_json.get("jumpData", {})
    #                 page_path = jump_data.get("pagePath", "")
    #
    #                 match = re.search(r'promotionId=([A-Za-z0-9]+)', page_path)
    #                 if match:
    #                     promotion_id = match.group(1)
    #                     fn_print(f"promotionId: {promotion_id}")
    #                     self.promotionID = promotion_id  # Return the first found promotionId
    #         fn_print("❌ 未找到 promotionID")
    #
    #     except Exception as e:
    #         fn_print(f"❌ 获取 promotionID 异常: {e}")

    def get_token(self) -> None:
        try:
            response = self.client.post(
                url="https://stdcrm.dtmiller.com/std-weixin-mp-service/miniApp/custom/login",
                headers=self.base_headers,
                json={"code": self.__code, "appId": app_id}
            ).json()

            if response['code'] == 0:
                self.token = response['data']
                fn_print(f"✅ 获取 token 成功")

            else:
                fn_print(f"❌ 获取 token 失败: {response.get('msg')}")
        except Exception as e:
            fn_print(f"⚠️ 获取 token 发生异常: {e}")

    def sign(self) -> None:
        self.get_integral()
        try:
            response = self.client.get(
                url="https://stdcrm.dtmiller.com/scrm-promotion-service/promotion/sign/today",
                headers=self.headers,
                params={
                    "promotionId": "PI67c25977540856000aac6ac0"
                }
            )
            if response.status_code == 200:
                response_data = response.json()
                if response_data['code'] == 0:
                    fn_print(f"用户【{self.user}】 -  签到成功！获得{response_data['data']['prize']['goodsName']} - "
                             f"签到天数： {response_data['data']['signDays']}")
                else:
                    fn_print(f"用户【{self.user}】 -  签到失败: {response_data['msg']}")
            else:
                fn_print(f"用户【{self.user}】 -  签到失败: {response.text}")
        except Exception as e:
            fn_print(f"用户【{self.user}】 -  签到发生异常: {e}")

    def get_integral(self) -> None:
        try:
            response = self.client.get(
                url="https://stdcrm.dtmiller.com/scrm-promotion-service/mini/wly/user/info",
                headers=self.headers
            ).json()
            # print(json.dumps(response, indent=4, ensure_ascii=False))
            if response['code'] == 0:
                self.user = response['data']['member']['mobile']
                fn_print(f"用户【{self.user}】 - 当前积分{response['data']['member']['points']}")
            else:
                fn_print(f"查询积分失败: {response['msg']}")
        except Exception as e:
            fn_print(f"查询积分发生异常: {e}")


def process_users(wxids, tokens) -> None:
    """
    :param wxids:
    :param tokens:
    :return:
    """
    padded_tokens = tokens + [None] * (len(wxids) - len(tokens)) if len(tokens) < len(wxids) else tokens
    user_accounts = list(zip(wxids, padded_tokens))
    total_users = len(user_accounts)

    if not user_accounts:
        fn_print("❌ 未配置 token 退出！")
        return
    elif not wxcenter:
        fn_print("⚠️ 未配置 wxcode server 退出！")
        return

    fn_print(f"🔍 共找到{total_users}个账号")

    for index, (wxid, token) in enumerate(user_accounts, start=1):
        fn_print(f"======🔄 开始执行第{index}个账号任务======")

        try:
            nwjg = Nwjg(token=token, wxid=wxid)

            # 获取code
            if wxid and not token:
                nwjg.get_wxcode()

            nwjg.sign()

            fn_print("-----------账号任务执行完毕-----------")

        except ValueError as e:
            fn_print(f"❌ 配置错误: {str(e)}")
        except Exception as e:
            fn_print(f"❌ 处理用户时出错: {str(e)}")


if __name__ == '__main__':
    process_users(wxid_nwjg, nwjg_tokens)
