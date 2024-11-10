from Crypto.Cipher import AES,PKCS1_v1_5
from Crypto.PublicKey import RSA
import msgpack
import uuid
import requests
import base64
import json
import urllib

class SekaiUser(object):
    
    def __init__(self, lid, iid, deviceId):
        self.lid = lid
        self.iid = iid
        self.deviceId = deviceId
        

class SekaiClient(object):
    
    def __init__(self, user:SekaiUser=None):
        self.urlroot = "https://mkkorea-obt-prod01-cdn.bytedgame.com/api"
        self.urlroot2 = "https://mkkorea-obt-prod02.bytedgame.com/api"
        self.headers = {
            "Content-Type": "application/octet-stream",
            "Accept": "application/octet-stream",
            "Accept-Encoding": "deflate, gzip",
            "Host": "mkkorea-obt-prod01-cdn.bytedgame.com",
            "User-Agent": "UnityPlayer/2020.3.32f1 (UnityWebRequest/1.0, libcurl/7.80.0-DEV)",
            "X-Install-Id": "8762943b-39c0-4716-9d9d-89b4b3382415",
            "X-App-Version": "3.4.0.15133",
            "X-App-Hash": "a3015fe8-785f-27e1-fb8b-546a23c82c1f",
            "X-Data-Version": "3.4.0.13",
            "X-Asset-Version": "3.4.0",
            "X-Platform": "Android",
            "device_id": user.deviceId,
            "X-DeviceModel": "Samsung SM-X710",
            "X-OperatingSystem": "Android OS 12 / API-32 (SP2A.220505.003/14.0.609_230420)",
            "X-Unity-Version": "2020.3.32f1"
            }
        self.headers["X-Request-Id"] = user.lid
        self.user = user
        
    @staticmethod
    def pack(content):
        mode = AES.MODE_CBC
        key = b"g2fcC0ZczN9MTJ61"
        iv = b"msx3IV0i9XE5uYZ1"
        cryptor = AES.new(key,mode,iv)
        ss = msgpack.packb(content)
        padding = lambda s: s + (16 - len(s) % 16) * chr(16 - len(s) % 16).encode()
        ss = padding(ss)
        return cryptor.encrypt(ss)
    
    @staticmethod
    def unpack(encrypted):
        mode = AES.MODE_CBC
        key = b"g2fcC0ZczN9MTJ61"
        iv = b"msx3IV0i9XE5uYZ1"
        cryptor = AES.new(key, mode, iv)
        plaintext = cryptor.decrypt(encrypted)
        return msgpack.unpackb(plaintext[:-plaintext[-1]],strict_map_key = False)

    def callapi(self, apiurl, method, content=None, root=None, hd=None):
        content = None if not content else self.pack(content)
        print(self.urlroot2+apiurl if root==None else root+apiurl)
        resp = requests.request(method, url=self.urlroot2+apiurl if root==None else root+apiurl, headers=self.headers if hd==None else hd, data=content, timeout=5)
        # print(resp.content)
        return self.unpack(resp.content)

    def calluserapi(self, apiurl, method, content=None):
        return self.callapi(f"/user{apiurl}", method, content, root=self.urlroot)
    
    # def register(self) -> SekaiUser:
    #     data = self.callapi("/user", "POST", {'platform': self.headers["X-Platform"], 'deviceModel': self.headers["X-DeviceModel"], 'operatingSystem': self.headers["X-OperatingSystem"]})
    #     credential = data["credential"]
    #     uid = data["userRegistration"]["userId"]
    #     self.user = SekaiUser(uid, credential)
    #     return self.user

    def getAccessToken(self, lid):
        url_visitor = "https://gsdk-sg.bytegsdk.com/sdk/account/"
        url_login = "https://gsdk-sg.bytegsdk.com/gsdk/account/"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'User-Agent': 'com.pjsekai.kr.oscb/15133 (Linux; U; Android 12; ko_KR; SM-X710; Build/SP2A.220505.003; Cronet/TTNetVersion:c10fb468 2023-04-11 QuicVersion:b314d107 2021-11-24)',
        }
        params = {
            "iid": user.iid,
            "device_id": user.deviceId,
            "ac": "wifi",
            "channel": "onestore",
            "aid": "292248",
            "app_name": "mk_korea",
            "device_platform": "android",
            "os": "android",
            "ssmix": "a",
            "device_type": "SM-X710",
            "device_brand": "Samsung",
            "language": "ko",
            "os_api": "32",
            "os_version": "12",
            "manifest_version_code": "15133",
            "sdk_language": "ko_KR",
            "login_way": "guest",
            "sys_region": "KR",
            "sdk_app_id": "1782",
            "tz_offset": "36000",
            "channel_op": "bsdkintl",
            "sdk_version": "2024.1.0.0",
            "game_id": "292248"
        }
        data_visitor = {
            "login_id": lid,
            "user_type": "1",
            "ui_flag": "1",
            "is_create": "0"
        }
        data_login = {
            "login_id": lid,
            "adjust_id": "",
            "device_id": user.deviceId,
            "iid":	user.iid,
            "login_type":	"history",
            "ui_flag":	"1",
            "channel_id":	"bsdkintl"
        }
        resp = requests.post(url=url_visitor+'visitor_login', params=params, data=data_visitor)
        res = json.loads(resp.content)
        print(res)
        data_login['data'] = json.dumps({'user_id':str(res['data']['user_id']),'token':str(res['data']['token'])})
        # print(data_login)
        resp = requests.post(url=url_login+'login', params=params, data=data_login)
        # print(resp.request.body)
        print(resp.content)
        res = json.loads(resp.content)
        return res['data']['access_token']
        
    def login(self):
        accessToken = self.getAccessToken(user.lid)
        data = self.calluserapi("/auth", "POST", {"accessToken": accessToken, "deviceId": None, "UserID": 0})
        # print(data)
        self.token = data["sessionToken"]
        self.headers["X-Session-Token"] = self.token
        return self.token
    
    def get_profile(self, uid:str):
        data = self.calluserapi("/{}/profile".format(uid), "GET")
        return data
        
    def test(self):
        pass

with open('config.json', 'r') as f:
    config = json.load(f)

uuId = config['uuId']
loginId = config['loginId']
iid = config['iid']

friendId = ""

user = SekaiUser(uuId, loginId, iid)
sekai = SekaiClient(user)
#  sekai.register()
sekai.login()
a = sekai.get_profile(friendId)
print(a)
# # print(a)

# output = base64.b64decode(b64.encode())
# result = sekai.unpack(output)
# with open('output.json', 'w', encoding='utf-8') as f:
#     json.dump(result, f, ensure_ascii=False, indent=4)