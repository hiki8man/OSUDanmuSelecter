import aiohttp
import time
import asyncio

map_type = {"b":"beatmaps",
            "s":"beatmapsets"}
class OsuApiV2:
    TOKEN_URL = r"https://osu.ppy.sh/oauth/token"
    APIV2_URL = r"https://osu.ppy.sh/api/v2"
    CLIENT_ID:int = -1
    CLIENT_SECRET:str = "get_key_on_osu_website"

    def __init__(self, client_id:int=-1, client_secret:str="") -> None:
        self.token:str = ""
        self.head_token:dict[str,str] = {"Authorization":"Bearer none"}
        self.archive_time:int = -1
        self.expires_time:int = -1
        asyncio.run(self.archive_token())

    async def check_token(self) -> bool:
        """
        检测token
        """
        if self.head_token["Authorization"] == "Bearer none" or self.expires_time < 0:
            return False
        elif (time.time() - self.archive_time) > self.expires_time - 5:
            return await self.archive_token()
        else:
            return True
        
    async def session_post(self,session:aiohttp.ClientSession, url:str, json_data:dict|None = None, use_ssl:bool=False) -> dict:
        async with session.post(url, json=json_data, ssl=use_ssl) as response:
            match response.status:
                case 200|201:
                    return await response.json()
                case __:
                    print(await response.text())
                    return {}
        return {}
    
    async def session_get(self,session:aiohttp.ClientSession, url:str, json_data:dict|None = None, use_ssl:bool=False) -> dict:
        async with session.get(url, json=json_data, ssl=use_ssl) as response:
            match response.status:
                case 200|201:
                    return await response.json()
                case __:
                    print(await response.text())
                    return {}
        return {}
        
    async def archive_token(self) -> bool:
        """
        获取token  
        直接赋值给self变量，使用初始值检测的方式确认是否数据有误
        """
        client_data:dict = {
            "client_id": OsuApiV2.CLIENT_ID,
            "client_secret": OsuApiV2.CLIENT_SECRET,
            "grant_type": "client_credentials",
            "scope": "public"
            }
        try:
            async with aiohttp.ClientSession() as session:
                token_data = await self.session_post(session, OsuApiV2.TOKEN_URL, client_data, False)
                if token_data:
                    self.archive_time = int(time.time())
                    self.expires_time = token_data["expires_in"]
                    self.head_token["Authorization"] = f"{token_data["token_type"]} {token_data["access_token"]}"
                    return True
        except Exception:
            #如果无法获取就赋值初始值
            self.head_token["Authorization"] = "Bearer none"
            self.archive_time = -1
            self.expires_time = -1

        return False
    
    async def get_api_info(self, api_suffix:str, json_data:dict|None = None) -> dict:
        if await self.check_token():
            async with aiohttp.ClientSession(headers=self.head_token) as session:
                return await self.session_get(session, f"{OsuApiV2.APIV2_URL}/{api_suffix}", json_data, True)
        else:
            return {}

v2_api = OsuApiV2()

@register_info_server("osu_v2")
async def get_info_kitsu(mapid_type:str, mapid_num:int) -> dict[str,str]|None:
    # kitsu镜像站获取谱面信息  
    # 先获取beatmapsets地址，再根据id类型把链接拼起来
    json_data = await v2_api.get_api_info(f"{map_type[mapid_type]}/{mapid_num}")
    # 更换mapid类型尝试二次搜索
    if not json_data:
        mapid_type = "s" if mapid_type == "b" else "b"
        json_data = await v2_api.get_api_info(f"{map_type[mapid_type]}/{mapid_num}")

    if json_data:
        map_info = {"server": "osu_v2",
                    "artist": json_data["artist"],
                    "title" : json_data["title"],
                    "sid"   : json_data["id"],
                    "url"   : f"https://osu.ppy.sh/beatmapsets/{json_data["id"]}"
                    }
        if mapid_type == "b":
            for beatmap in json_data["beatmapset_id"]:
                if beatmap["id"] == mapid_num:
                    map_info["url"] = f"{map_info["url"]}#{beatmap["mode"]}/{mapid_num}"
                    
        return map_info

if __name__ = "__init__":
    osu_api = OsuApiV2()

    info = asyncio.run(osu_api.get_api_info("beatmaps/5265618"))
    info2 = asyncio.run(osu_api.get_api_info("beatmapsets/2410920"))
    info3 = asyncio.run(osu_api.get_api_info("users/15846580/recent_activity"))
    pass