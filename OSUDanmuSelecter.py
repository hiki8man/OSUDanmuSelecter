import asyncio, aiohttp
import http.cookies
import blivedm
import blivedm.models.web as web_models
import json
from irc_api import AsyncIRCClient
from info_api import get_info as get_beatmap_info
from pprint import pprint
import re

with open("setting.json","rb") as f:
    setting = json.load(f)

USER_NAME:str = setting["osu_username"]
PASSWORD:str = setting["irc_password"]
ROOMID:str = setting["bili_room_id"]
API_SERVER:str = setting["api_server"]

if USER_NAME == "":
    raise ValueError("请在setting.json设置你的OSU用户名")
if PASSWORD == "":
    raise ValueError("请在setting.json设置irc密码")
if ROOMID == "":
    raise ValueError("请在setting.json设置直播间房间号")
if API_SERVER == "":
    print("没有设置获取谱面信息API，将默认使用sayobot")
    API_SERVER = "sayo"

irc = AsyncIRCClient(
    host="irc.ppy.sh",
    port=6667,
    nick=USER_NAME,
    password=PASSWORD
)

def get_mapid(danmu_text:str) -> str|None:
    # 收到明确表名为sid或bid
    match = re.match(r"^(?:点歌[\s]?/?)?([bBsS]\d+)",danmu_text)
    if match:
        return match.group(1).lower()

    # 只发了纯数字，处理为bid
    match = re.match(r"^点歌[\s]?/?(\d+)",danmu_text)
    if match:
        return f"b{match.group(1)}"

async def send_beatmap_url(mapid:str,commit:str="") -> None:
    beatmapinfo:dict|None = await get_beatmap_info(mapid[0], int(mapid[1:]), API_SERVER)
    if beatmapinfo:
        pprint(beatmapinfo)
        map_url:str = beatmapinfo["url"]
        sid = beatmapinfo["sid"]
        beatmap_msg = " ".join([f"收到弹幕点歌：[{map_url} {beatmapinfo["artist"]} - {beatmapinfo["title"]}]",
                                f"Sayo分流：[https://osu.sayobot.cn/home?search={sid} osu.sayobot.cn]",
                                f"kitsu分流：[https://osu.direct/beatmapsets/{sid} osu.direct]",
                                ])
    else:
        # 如果无法正常获取谱面信息则直接返回链接，不考虑正确性
        beatmap_msg = f"收到弹幕点歌：https://osu.ppy.sh/{mapid[0]}/{mapid[1:]}"
    print("正在发送信息")
    await send_msg(beatmap_msg, is_action=True)
    print("发送信息完成")


async def send_msg(msg:str, target_name:str=USER_NAME, is_action:bool=False):
    # 给自己发送消息
    if is_action:
        msg = f"\x01ACTION {msg}\x01"
    await irc.send_privmsg(target_name, msg)

# 这里填一个已登录账号的cookie的SESSDATA字段的值。不填也可以连接，但是收到弹幕的用户名会打码，UID会变成0
SESSDATA = ''

session: aiohttp.ClientSession|None = None

def init_session():
    cookies = http.cookies.SimpleCookie()
    cookies['SESSDATA'] = SESSDATA
    cookies['SESSDATA']['domain'] = 'bilibili.com'

    global session
    session = aiohttp.ClientSession()
    session.cookie_jar.update_cookies(cookies)

async def run_single_client():
    room_id = int(ROOMID)
    client = blivedm.BLiveClient(room_id, session=session)
    handler = MyHandler()
    client.set_handler(handler)
    client.start()
    

class MyHandler(blivedm.BaseHandler):

    def _on_danmaku(self, client: blivedm.BLiveClient, message: web_models.DanmakuMessage):
        map_id = get_mapid(message.msg)
        if map_id:
            print(f"弹幕点歌 {map_id}")
            asyncio.create_task(send_beatmap_url(str(map_id)))

async def main():
    init_session()
    await asyncio.gather(
        run_single_client(),
        irc.connect()
    )


asyncio.run(main())
