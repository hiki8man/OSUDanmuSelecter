from irc_api import AsyncIRCClient
import asyncio
import aiohttp
import http.cookies
from typing import *
import blivedm
import blivedm.models.web as web_models
import json
from info_api import get_info as get_beatmap_info
from pprint import pprint
# ----------------------------
# 测试示例
# ----------------------------
with open("setting.json","rb") as f:
    setting = json.load(f)

USER_NAME:str = setting["osu_username"]
PASSWORD:str = setting["irc_password"]
ROOMID:str = setting["bili_room_id"]

if USER_NAME == "":
    raise ValueError("请在setting.json设置你的OSU用户名")
if PASSWORD == "":
    raise ValueError("请在setting.json设置irc密码")
if ROOMID == "":
    raise ValueError("请在setting.json设置直播间房间号")

irc = AsyncIRCClient(
    host="irc.ppy.sh",
    port=6667,
    nick=USER_NAME,
    password=PASSWORD  # 修改为 "你的密码" 如果有
)

def check_mapid(mapid:str) -> bool:
    return mapid[0] == "s" or  mapid[0] == "b"

async def get_beatmap_url_ppy(mapid:str) -> str:
    #搜不到用官网搜
    ppy_url = f"https://osu.ppy.sh/{mapid[0]}/{mapid[1:]}"
    print("正在获取链接")
    async with aiohttp.ClientSession() as session:
        async with session.get(ppy_url, allow_redirects=True) as resp:
            return str(resp.url)

async def send_beatmap_url(mapid:str) -> None:
    print("获取谱面信息")
    beatmapinfo = await get_beatmap_info(mapid[0], int(mapid[1:]), "sayo")
    if beatmapinfo:
        pprint(beatmapinfo)
        map_url:str = beatmapinfo["url"]
        sid = beatmapinfo["sid"]
        beatmap_msg = f"弹幕点歌：[{map_url} {beatmapinfo["artist"]} - {beatmapinfo["title"]}]"

        if beatmapinfo["server"] == "sayo":
            beatmap_msg += " Sayo分流："
            beatmap_msg += f"[https://txy1.sayobot.cn/beatmaps/download/{sid}?server=auto (带视频)]/"
            beatmap_msg += f"[https://txy1.sayobot.cn/beatmaps/download/novideo/{sid}?server=auto (无视频)]"
    else:
        print("获取失败，将通过官网获取Baetmapset地址")
        map_url:str = await get_beatmap_url_ppy(mapid)
        sid = map_url.split("/")[-1]
        beatmap_msg = f"弹幕点歌: {map_url}"

    print("正在发送信息")
    await send_msg(beatmap_msg)
    print("发送信息完成")


async def send_msg(msg:str, target_name:str=USER_NAME):
    # 给自己发送消息
    await irc.send_message(target_name, msg)

# 这里填一个已登录账号的cookie的SESSDATA字段的值。不填也可以连接，但是收到弹幕的用户名会打码，UID会变成0
SESSDATA = ''

session: Optional[aiohttp.ClientSession] = None

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
            case [command,ID] if command.lower() == "点歌" and check_mapid(ID) :
                print(f"弹幕点歌 {ID}")
                asyncio.create_task(send_beatmap_url(str(ID)))

async def main():
    init_session()
    await asyncio.gather(
        run_single_client(),
        irc.connect()
    )

    
asyncio.run(main())
