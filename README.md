# Kook 音乐机器人

## 安装
建议使用python 3.8，支持3.8-3.10
```shell
pip install enum
pip install khl.py
pip install aiohttp
pip install asyncio
```
或者直接用`requirement.txt`安装

此代码已集成[simple-kook-voice](https://github.com/Edint386/simple-kook-voice)，感谢其提供的推流模块

## 启动
启动前请在main.py同级目录新建`config.json`并填写以下内容：
```json
{
    "token": "机器人token",
    "ffmpeg": "ffmpeg可执行文件位置"
}
```

然后使用`python main.py`启动

## 使用
**使用指令前请务必进入一个语音频道！**

`/菜单` `/menu` 打开控制台

`/搜歌 <关键词>` 搜索歌曲（使用网易云）

**注意：如果关键词有空格，请使用下划线代替！**

`/播放 <url>` 直链播放歌曲 **不建议使用**

`/join` **已过时** 强制把机器人拉到自己的语音频道

`/切歌` `/跳过` **已过时** 顾名思义，已集成到控制台

`/停止` **已过时** 停止播放，已集成到控制台

`/列表` **已过时** 显示播放列表，已集成到控制台

`/跳转 <秒数>` 调整播放的位置，**未测试**