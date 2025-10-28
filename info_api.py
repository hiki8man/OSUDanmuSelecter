import aiohttp, asyncio
import json
from typing import Any
from collections.abc import Callable

GET_INFO_COMMON: dict[str, Callable[[str, int], Any]] = {}
TIMEOUT = 8

async def get_url_json(url:str) -> dict:
    """
    使用aiohttp获取json信息  
    如果没有信息就返回空字典  
    由于sayo镜像站使用的json返回有问题，因此需要解析为text再解析回json
    """
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=TIMEOUT)) as session:
        async with session.get(url=url) as response:
            if response.status == 200:
                data_text = await response.text()
                return json.loads(data_text)
            return {}

def register_info_server(server_name:str):
    '''
    注册表装饰器，用于添加各类获取谱面信息的api函数
    '''
    def decorator(func):
        GET_INFO_COMMON[server_name] = func
        return func
    return decorator

async def get_info(mapid_type:str, mapid_num:int, server_name:str|None = None) -> dict|None:
    """
    获取谱面信息，如果获取失败将会返回None  
    返回的字典：  
    {"server": 所使用的API
     "artist": 艺术家信息,  
     "title" : 歌曲标题，
     "sid"   : BeatMapSetID  
     "url"   : 谱面链接"}  
    """
    get_info_common = GET_INFO_COMMON.copy()
    if server_name:
        print(f"正在尝试从{server_name}获取谱面信息")
        get_info = GET_INFO_COMMON[server_name]
        info = await get_info(mapid_type, mapid_num)
        if info:
            return info
        else:
            get_info_common.pop(server_name)
    
    for server_name in GET_INFO_COMMON:
        print(f"正在尝试从{server_name}获取谱面信息")
        get_info = GET_INFO_COMMON[server_name]
        info = await get_info(mapid_type, mapid_num)
        if info:
            return info
    print("获取谱面信息失败！镜像站没有该谱面或网络连接不佳")

import server