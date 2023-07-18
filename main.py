import asyncio
import json
import kookvoice
from khl import *
from khl.card import CardMessage, Card, Module, Element, Types, Struct
import music
import sys

with open('./config.json','r',encoding='utf8')as fp:
    config = json.load(fp)
    global bot_token
    bot_token=config['token']
    kookvoice.ffmpeg_bin=config['ffmpeg']

bot = Bot(token=bot_token)

async def find_user(gid, aid):
    global current_voice_channel
    # 调用接口查询用户所在的语音频道
    voice_channel_ = await bot.client.gate.request('GET', 'channel-user/get-joined-channel',
                                                   params={'guild_id': gid, 'user_id': aid})
    voice_channel = voice_channel_["items"]
    if voice_channel:
        vcid = voice_channel[0]['id']
        return vcid
    
musicIdUrlMap={}

@bot.command(name='whoisnigge')
async def ping(msg:Message):
    await msg.ctx.channel.send('NotLegit')

@bot.command(name='stop')
async def stop(msg:Message):
    sys.exit(0)

async def add_song(guild_id:str,author_id:str,song_url:str,extra_data):
    voice_channel_id = await find_user(guild_id, author_id)
    player = kookvoice.Player(guild_id, voice_channel_id, bot_token)
    player.add_music(song_url, extra_data)
 
async def on_message(msg:Message):
    print(f'''{msg.author.nickname}({msg.author_id}) [{msg.ctx.channel.id}] {msg.content}''')
    if(msg.type==MessageTypes.TEXT or msg.type==MessageTypes.KMD):
        if(msg.content.startswith('/搜歌 ')):
            keyword=msg.content.replace('/搜歌 ','')
            global musicIdUrlMap
            d = {"hlpretag": "<span class=\"s-fc7\">", "hlposttag": "</span>", "s": keyword, "type": "1", "offset": "0",
                "total": "true", "limit": "30", "csrf_token": ""}
            d = json.dumps(d)
            random_param = music.get_random()
            param = music.get_final_param(d, random_param)
            song_list = music.get_music_list(param['params'], param['encSecKey'])
            c = Card()
            c.append(Module.Section('搜索关键词：'+keyword))
            c.append(Module.Divider())
            if len(song_list) > 0:
                song_list = json.loads(song_list)['result']['songs']
                for i, item in enumerate(song_list):
                    item = json.dumps(item)
                    song_id=str(json.loads(str(item))['id'])
                    name=json.loads(str(item))['name'] + ' - ' + json.loads(str(item))['ar'][0]['name']
                    d = {"ids": "[" + song_id + "]", "level": "standard", "encodeType": "",
                         "csrf_token": ""}
                    d = json.dumps(d)
                    param = music.get_final_param(d, random_param)
                    song_info = music.get_reply(param['params'], param['encSecKey'])
                    if len(song_info) > 0:
                        song_info = json.loads(song_info)
                        song_url = json.dumps(song_info['data'][0]['url'], ensure_ascii=False)
                        musicIdUrlMap[song_id] = [song_url.replace('"',''),name]
                        c.append(Module.Section(name,Element.Button('点歌','play-' + song_id,Types.Click.RETURN_VAL,'primary')))
                    # else:
                    #     ret += "\n该首歌曲解析失败，可能是因为歌曲格式问题"
            else:
                c.append(Module.Section('很抱歉，未能搜索到相关歌曲信息'))
            await msg.ctx.channel.send(CardMessage(c))

bot.add_message_handler(on_message,[MessageTypes.AUDIO,MessageTypes.CARD,MessageTypes.FILE,MessageTypes.IMG,MessageTypes.SYS,MessageTypes.VIDEO])   

@bot.on_event(EventTypes.MESSAGE_BTN_CLICK)
async def on_button_click(bot: Bot, e: Event):
    global musicIdUrlMap
    print(f'''{e.body['user_info']['nickname']} took the {e.body['value']} pill''')
    values = str(e.body['value']).split('-')
    key = values[0]
    arg = values[1]
    if(key == 'play'):
        if(musicIdUrlMap.get(arg) is not None):
            await add_song(e.body['guild_id'],e.body['user_info']['id'],musicIdUrlMap.get(arg)[0],{"音乐名字": musicIdUrlMap.get(arg)[1], "点歌人": e.body['user_info']['nickname']})
            channel = PublicTextChannel(_gate_ = bot.client.gate, id = e.body['target_id'])
            await channel.send(CardMessage(Card(Module.Header('添加音乐成功'),Module.Divider(),Module.Section('歌曲：' + musicIdUrlMap.get(arg)[1]),Module.Section('点歌人：'+e.body['user_info']['nickname']))))
    if(key == 'control'):
        channel = PublicTextChannel(_gate_ = bot.client.gate, id = e.body['target_id'])
        player = kookvoice.Player(e.body['guild_id'])
        if(arg == 'list'):
            try:
                music_list = player.list()
            except Exception:
                c = Card()
                c.append(Module.Section('当前没有正在播放的歌曲'))
                await channel.send(CardMessage(c))
                return
            c = Card()
            c.append(Module.Section('正在播放'))
            c.append(Module.Header(f"{music_list[1]['音乐名字']}"))
            c.append(Module.Section(f"点歌人：{music_list[1]['点歌人']}"))
            c.append(Module.Divider())
            c.append(Module.Section(f"列表中歌曲"))
            if(music_list[2]==[]):
                c.append(Module.Section(f"无更多歌曲"))
            else:
                paragraph = Struct.Paragraph(2,Element.Text('**歌曲**'))
                paragraph.append(Element.Text('**点歌人**'))
                for index, i in enumerate(music_list[2]):
                    # 这里的extra data 便是点歌的时候放入的东西
                    paragraph.append(Element.Text(f"{index + 1}. {i['音乐名字']}"))
                    paragraph.append(Element.Text(i['点歌人']))
                c.append(Module.Section(paragraph))
            print(json.dumps(CardMessage(c)))
            await channel.send(CardMessage(c))
        elif(arg == 'skip'):
            # 在当前服务器歌单有歌曲的时候，你可以直接填入guild_id来获取player
            player.skip()
            await channel.send(f'已跳过当前歌曲')
        elif(arg == 'stop'):
            player.stop()
            await channel.send(f'播放已停止')

# 让点歌机加入频道
# 这条指令其实完全没用，因为点歌了会自动加入语音频道
# 但是还是写了，万一有人要呢
# 指令： /join
@bot.command(name='join')
async def join_vc(msg:Message):
    # 获取用户所在频道
    voice_channel_id = await find_user(msg.ctx.guild.id, msg.author_id)
    if voice_channel_id is None:
        await msg.ctx.channel.send('请先加入语音频道')
        return
    player = kookvoice.Player(msg.ctx.guild.id, voice_channel_id, bot_token)
    player.join()
    voice_channel = await bot.client.fetch_public_channel(voice_channel_id)
    await msg.ctx.channel.send(f'已加入语音频道 #{voice_channel.name}')


# 播放直链或本地歌曲
# 指令： /播放 https://api.kookbot.cn/static/Ulchero,Couple%20N-LoveTrip.mp3
@bot.command(name='播放')
async def play(msg: Message, music_url: str):
    # 第一步：获取用户所在的语音频道
    voice_channel_id = await find_user(msg.ctx.guild.id, msg.author_id)
    # 如果不在语音频道就提示加入语音频道后点歌
    if voice_channel_id is None:
        await msg.ctx.channel.send('请先加入语音频道')
        return

    # 如果用户发了音乐直链，会被kook转为链接的kmd，要拆一下
    if 'http' in music_url and '[' in music_url:
        music_url = music_url.split('[')[1].split(']')[0]

    await add_song(msg.ctx.guild.id,msg.author_id,music_url,{"音乐名字": "未知", "点歌人": msg.author.nickname})
    await msg.ctx.channel.send(f'添加音乐成功')

    # 机器人提示点歌成功
    await msg.ctx.channel.send(f'添加音乐成功 {music_url}')

@bot.command(name='菜单')
async def show_menu_(msg: Message):
    await show_menu(msg)
@bot.command(name='menu')
async def show_menu(msg: Message):
    c = Card()
    c.append(Module.Header('控制台'))
    c.append(Module.Divider())
    c.append(Module.ActionGroup(Element.Button('列表','control-list',Types.Click.RETURN_VAL,'info')))
    c.append(Module.ActionGroup(Element.Button('切歌','control-skip',Types.Click.RETURN_VAL,'info'),Element.Button('停止','control-stop',Types.Click.RETURN_VAL,'info')))
    await msg.ctx.channel.send(CardMessage(c))


# 既然能够添加歌曲 那也得有控制选项
# 指令： /切歌 或者 /跳过
@bot.command(name='切歌')
async def skip_(msg: Message):
    await skip(msg)
@bot.command(name='跳过')
async def skip(msg: Message):
    # 在当前服务器歌单有歌曲的时候，你可以直接填入guild_id来获取player
    player = kookvoice.Player(msg.ctx.guild.id)
    player.skip()
    await msg.ctx.channel.send(f'已跳过当前歌曲')

# 指令： /停止
@bot.command(name='停止')
async def stop(msg: Message):
    player = kookvoice.Player(msg.ctx.guild.id)
    player.stop()
    await msg.ctx.channel.send(f'播放已停止')

from khl.card import Module, Card, CardMessage

# 指令： /列表
@bot.command(name="列表")
async def list(msg: Message):
    player = kookvoice.Player(msg.ctx.guild.id)
    try:
        music_list = player.list()
    except Exception:
        c = Card()
        c.append(Module.Section('当前没有正在播放的歌曲'))
        await msg.ctx.channel.send(CardMessage(c))
        return
    c = Card()
    c.append(Module.Section('正在播放'))
    c.append(Module.Header(f"{music_list[1]['音乐名字']}"))
    c.append(Module.Section(f"点歌人：{music_list[1]['点歌人']}"))
    c.append(Module.Divider())
    c.append(Module.Section(f"列表中歌曲"))
    if(music_list[2]==[]):
        c.append(Module.Section(f"无更多歌曲"))
    else:
        paragraph = Struct.Paragraph(2,[Element.Text('歌曲'),Element.Text('点歌人')])
        for index, i in enumerate(music_list[2]):
            # 这里的extra data 便是点歌的时候放入的东西
            paragraph.append(f"{index + 1}. {i['音乐名字']}")
            paragraph.append(i['点歌人'])
        c.append(Module.Section(paragraph))
    await msg.ctx.channel.send(CardMessage(c))


# 指令： /跳转 120
# 注：120是秒数
@bot.command(name="跳转")
async def seek(msg: Message, time: int):
    player = kookvoice.Player(msg.ctx.guild.id)
    player.seek(time)
    await msg.ctx.channel.send(f'已跳转到 {time} 秒')


# 切歌时触发事件便于发送开始的消息
@kookvoice.on_event(kookvoice.Status.START)
async def on_music_start(play_info: kookvoice.PlayInfo):
    print(play_info)
    guild_id = play_info.guild_id
    voice_channel_id = play_info.voice_channel_id
    music_bot_token = play_info.token
    extra_data = play_info.extra_data  # 你可以在这里获取到歌曲的备注信息
    text_channel_id = extra_data['文字频道']
    text_channel = await bot.client.fetch_public_channel(text_channel_id)
    await text_channel.send(f"正在播放 {play_info.file}")


if __name__ == '__main__':
    loop=''
    try:
        loop=asyncio.get_event_loop()
    except:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    # 使用gather同时启动机器人与推流
    loop.run_until_complete(asyncio.gather(bot.start(), kookvoice.start()))