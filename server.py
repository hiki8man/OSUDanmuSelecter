from info_api import get_url_json, register_info_server

OSU_MODE:tuple = ("#osu", "#taiko", "#fruits", "#mania")

@register_info_server("sayo")
async def get_info_sayo(mapid_type:str, mapid_num:int) -> dict[str,str]|None:
    '''
    sayo镜像站获取谱面信息  
    '''
    json_data = await get_url_json(f"https://api.sayobot.cn/v2/beatmapinfo?0={mapid_num}")
    if json_data:
        map_info = {"server": "sayo",
                    "artist": json_data["data"]["artist"],
                    "title" : json_data["data"]["title"],
                    "sid"   : json_data["data"]["sid"],
                    "url"   : f"https://osu.ppy.sh/beatmapsets/{json_data["data"]["sid"]}"
                    }
        
        # sayo站能自动根据bid和sid搜索，这里利用sid进行了二次检测
        if mapid_type == "b" and mapid_num != json_data["data"]["sid"]:
            map_mode = OSU_MODE[json_data["data"]["bid_data"][0]["mode"]]
            map_info["url"] = f"{map_info["url"]}#{map_mode}/{mapid_num}"

        return map_info

@register_info_server("kitsu")
async def get_info_kitsu(mapid_type:str, mapid_num:int) -> dict[str,str]|None:
    '''
    kitsu镜像站获取谱面信息  
    '''
    json_data = await get_url_json(f"https://osu.direct/api/v2/{mapid_type}/{mapid_num}")
    # 更换mapid类型尝试二次搜索
    if not json_data:
        mapid_type = "s" if mapid_type == "b" else "b"
    json_data = await get_url_json(f"https://osu.direct/api/v2/{mapid_type}/{mapid_num}")

    if json_data:
        map_info = {"server": "kitsu",
                    "artist": json_data["artist"],
                    "title" : json_data["title"]
                    }
        if mapid_type == "s":
            map_info["sid"] = json_data["id"]
            map_info["url"] = f"https://osu.ppy.sh/beatmapsets/{json_data["id"]}"
        if mapid_type == "b":
            map_info["sid"] = json_data["beatmapset_id"]
            map_info["url"] = f"https://osu.ppy.sh/beatmapsets/{json_data["beatmapset_id"]}/#{json_data["mode"]}/{json_data["id"]}"

        return map_info