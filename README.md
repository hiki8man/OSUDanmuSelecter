![效果演示](https://github.com/hiki8man/OSUDanmuSelecter/blob/main/image/preview.jpg)
基于Blivedm库实现的OSU弹幕点歌机  
受到IRC私信方式限制不支持Lazer


设置：

前往你自己账号的这个网址
https://osu.ppy.sh/home/account/edit
往下拉找到 旧版API 启用irc

右键编辑打开setting.json
```
{
    "osu_username":"(你的osu用户名)",
    "irc_password":"(你的irc客服端密码)",
    "bili_room_id":"(你的房间ID)",
    "api_server":"sayo",
}
```
启动OSUDanmuSelecter.py即可

弹幕指令：  
点歌 b(bid)  
点歌 s(sid)

其他设置：  
```
api_server可以设置 osu_html, sayo, kitsu，设置后将会从指定的服务器获取谱面信息
osu_html:从官网爬取页面信息获取谱面信息
sayo：从sayo镜像站api获取谱面信息
kitsu：从kitsu镜像站api获取谱面信息
```
你也可以通过魔改server.py添加其他API支持

