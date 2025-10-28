import asyncio, aiohttp
import http.cookies
import blivedm
import blivedm.models.web as web_models
import json
from irc_api import AsyncIRCClient
from info_api import get_info as get_beatmap_info
from pprint import pprint
import re

TIMEOUT = 16

with open("setting.json","rb") as f:
    setting = json.load(f)

USER_NAME:str = setting["osu_username"]
PASSWORD:str = setting["irc_password"]
ROOMID:str = setting["bili_room_id"]
API_SERVER:str = setting["api_server"]
UNSAFE_MODE:bool = setting["unsafe_mode"]

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

def check_mapid(mapid:str) -> bool:
    try:
        int(mapid[1:])
        return mapid[0] == "s" or mapid[0] == "b"
    except ValueError:
        return False

async def get_beatmap_unsafe(mapid:str) -> str:
    # 通过官网跳转地址获取
    ppy_url = f"https://osu.ppy.sh/{mapid[0]}/{mapid[1:]}"
    print("正在获取链接")
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=TIMEOUT)) as session:
        async with session.get(ppy_url, allow_redirects=True) as resp:
            # 如果使用bid则添加#osu后缀，经测试可以正常跳转谱面
            if mapid[0] == "b":
                map_url = f"{str(resp.url)}#osu/{mapid[1:]}"
            else:
                map_url = str(resp.url)
            print("尝试获取谱面标题")
            html = await resp.text()
            match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
            if match:
                title = match.group(1)[:match.group(1).rfind(" · ")]
                print(f"{title}")
                return f"[{map_url} {title}]"
            else:
                print(f"获取失败")
                return f"{map_url}"

async def send_beatmap_url(mapid:str) -> None:
    # 如果启用unsafe_mode将会直接从官网获取链接
    beatmapinfo = None if UNSAFE_MODE else await get_beatmap_info(mapid[0], int(mapid[1:]), API_SERVER)
    if beatmapinfo:
        pprint(beatmapinfo)
        map_url:str = beatmapinfo["url"]
        sid = beatmapinfo["sid"]
        beatmap_msg = " ".join([f"收到弹幕点歌：[{map_url} {beatmapinfo["artist"]} - {beatmapinfo["title"]}]",
                                f"Sayo分流：[https://osu.sayobot.cn/home?search={sid} osu.sayobot.cn]",
                                f"kitsu分流：[https://osu.direct/beatmapsets/{sid} osu.direct]"
                                ])
    else:
        print("正在通过官网获取谱面地址")
        map_url:str = await get_beatmap_unsafe(mapid)
        sid = map_url.split("/")[-1]
        beatmap_msg = f"收到弹幕点歌: {map_url}"

    print("正在发送信息")
    await send_msg(beatmap_msg)
    print("发送信息完成")


async def send_msg(msg:str, target_name:str=USER_NAME):
    # 给自己发送消息
    await irc.send_message(target_name, msg)

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
        match message.msg.split(maxsplit=1):
            case [command,ID] if command.lower() == "点歌" and check_mapid(ID.lower()) :
                print(f"弹幕点歌 {ID.lower()}")
                asyncio.create_task(send_beatmap_url(str(ID.lower())))

async def main():
    init_session()
    await asyncio.gather(
        run_single_client(),
        irc.connect()
    )
    
asyncio.run(main())
