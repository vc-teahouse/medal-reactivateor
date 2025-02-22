"""
通过cookie登录bilibili，发送弹幕，用于保持粉丝牌激活状态
    key:crnmsmshsa (一句名场面而已)
"""

import os
import sys
import json
import random
from time import sleep,perf_counter
from loguru import logger
from dotenv import load_dotenv
from bilibili_api import Credential,Danmaku,user
from bilibili_api import sync,parse_link,select_client
from bilibili_api.live import LiveRoom
from bilibili_api.exceptions import ResponseCodeException,ApiException
from danmu_dict import danmu_list

level="WARNING"
select_client('aiohttp')
logger.add("reactivate.log",rotation="3 day",encoding="utf-8",backtrace=True,diagnose=True,level=level)

load_dotenv(dotenv_path="./.env")
c=Credential()
ignore_rooms=[]

try:
    ignore_rooms=os.environ['ignore'].split(",")
except KeyError:
    pass

with_qrcode=False

print(sys.argv)
if len(sys.argv) >= 2:
    if "-with-qrcode" in sys.argv:
        with_qrcode=True
    elif "-cookies" in sys.argv:
        with open(file=sys.argv[sys.argv.index("-cookies")+1],mode="r",encoding="utf-8",errors="ignore") as f:
            os.environ['cookies']=f.read()
    if "-roomids" in sys.argv:
        os.environ['roomids']=sys.argv[sys.argv.index("-roomids")+1]
    if "-ignore" in sys.argv and os.environ['roomids'] == "all":
        ignore_rooms=sys.argv[sys.argv.index("-ignore")+1].split(",")
        

def login(): # get cookie from env
    if with_qrcode:
        logger.info("等待用户扫码...")
        from blapi_port.login_port import login_with_qrcode
        c=login_with_qrcode()
        return c
    logger.info("正在通过env获取cookie")
    try:
        cookie=os.environ['cookies']
        cookie=dict(json.loads(cookie))
        c = Credential(
            sessdata=cookie.get('SESSDATA'),
            bili_jct=cookie.get('bili_jct'),
            buvid3=cookie.get('buvid3'),
            buvid4=cookie.get('buvid4'),
            dedeuserid=cookie.get('DedeUserID'),
            ac_time_value=cookie.get('ac_time_value')
            )
        if sync(c.check_refresh()):
            c.refresh()
            logger.info('Refresh cookie successfully!')
        else:
            logger.info('Cookie is still valid!')
    except:
        raise
    return c

sended_danmu=[]

def get_text():
    global sended_danmu
    text=random.choice(danmu_list)
    try:
        if text is sended_danmu[-1] or text is None:
            get_text()
        else:
            sended_danmu.append(text)
            return text
    except IndexError:
        sended_danmu.append(text)
        return text

def reactivate(): # main function
    global ignore_rooms
    roomids=os.environ['roomids']
    if roomids == "all":
        roomids=get_roomids_form_medal_list()
    else:    
        roomids=roomids.split(",")
    try:
        logger.info(f"直播间列表:{roomids}")
        sleep(5)
        for live_roomid in roomids:
            logger.debug(f"切换房间：{live_roomid}")
            if live_roomid in ignore_rooms:
                continue
            live_room = LiveRoom(room_display_id=live_roomid,credential=c)
            for i in range(1,11): # 发送10次弹幕
                sleep_time=5+random.random()
                text=get_text()
                logger.debug(f"第{i}次发送弹幕，内容为：{text},等待 {sleep_time:.2f}s")
                sync(live_room.send_danmaku(danmaku=Danmaku(text=text)))
                sleep(sleep_time)
            sended_danmu.clear()
    except:
        raise

def get_roomids_form_medal_list(): # get roomids from medal list(but user class doesn't work)
    user_self=sync((user.get_self_info(credential=c)))
    medal_list=sync(user.User(user_self['mid'],credential=c).get_user_medal())
    logger.info('Get medal list successfully!')
    medal_list=medal_list['list']
    roomids=[]
    failed_dict={}
    for i in medal_list:
        logger.info(f"获取当前牌子（{i['medal_info']['medal_name']}）的对应直播间号")
        logger.info(f"目前已成功获取的直播间号列表为：{roomids}")
        try:
            if i['link'].startswith('https://space.bilibili.com/'): # 通常情况下是这个链接
                logger.debug(f"获取到个人空间链接，尝试获取直播间号...")
                obj=sync(parse_link(url=i['link'],credential=c))[0]
                info=sync(obj.get_live_info()) # (上游已修复)(https://github.com/nemo2011/bilibili-api/issues/892)
                roomids.append(info['live_room']['roomid'])
            elif i['link'].startswith('https://live.bilibili.com'): # 这个链接在直播状态下才会有
                logger.debug(f"获取到直播间链接，直接从链接中提取直播间号...")
                roomid=i['link'].replace('https://live.bilibili.com/','')
                index=roomid.find('?')
                roomid=int(roomid[:index])
                roomids.append(roomid)
            else:
                logger.warning('Unknown link: '+i['link'])
        except ResponseCodeException as e:
            logger.warning(f"获取失败，原因：{e}，跳过")
            failed_dict[i['medal_info']['medal_name']]=e
            continue
        except ApiException as e:
            logger.critical(f"获取失败，原因：{e}，跳过")
            failed_dict[i['medal_info']['medal_name']]=e
            continue
        logger.debug(f"获取成功,直播间号：{roomids[-1]}")
    logger.warning(f"{failed_dict}")
    return roomids
    
    
if __name__ == "__main__":
    timer=perf_counter()
    c = login()
    logger.info("登录成功")
    reactivate()
    logger.info("已完成,耗时{:.2f}s".format(perf_counter()-timer))