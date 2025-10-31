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

async def get_response(source_url:str) -> tuple[str, str]:
    '''
    使用aiohttp获取重定向一次后的链接与网页信息  
    如果没有重定向则直接返回response的链接  
    只适用于OSU这种只重定向一次的情况，其他情况需要考虑更改代码
    '''
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=TIMEOUT)) as session:
        async with session.get(source_url, allow_redirects=False) as response:
            if response.status == 302 and "Location" in response.headers:
                target_url = response.headers["Location"]
                async with session.get(target_url) as response:
                    html_text = await response.text()
            if response.status == 200:
                target_url = str(response.url)
                html_text = await response.text()
            if response.status == 404:
                target_url = "404"
                html_text  = "404 not found"

    return (target_url, html_text)

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