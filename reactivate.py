"""
通过cookie登录bilibili，发送弹幕，用于保持粉丝牌激活状态
    key:crnmsmshsa
"""

import os
import sys
import json
import time
import random
from loguru import logger
from dotenv import load_dotenv
from bilibili_api import Credential,sync,Danmaku
from bilibili_api.live import LiveRoom
from danmu_dict import danmu_list

c=Credential()

print(sys.argv)
if len(sys.argv) >= 1:
    if sys.argv[1] == "dev":
        load_dotenv(dotenv_path="./.env")



def login(): # get cookie from env
    logger.info("正在通过env获取cookie")
    try:
        cookie=os.environ['cookies']
        cookie=dict(json.loads(cookie))
        c = Credential(
            sessdata=cookie.get('SESSDATA'),
            bili_jct=cookie.get('bili_jct'),
            buvid3=cookie.get('buvid3'),
            dedeuserid=cookie.get('DedeUserID'),
            ac_time_value=cookie.get('ac_time_value')
            )
    except:
        raise
    return c

def reactivate(): # main function
    roomids=os.environ['roomids']
    if roomids == "all":
        roomids=roomids.split(",") # WIP: get all roomids from medal_list
        pass
    else:    
        roomids=roomids.split(",")
    try:
        for live_roomid in roomids:
            logger.info(f"切换房间：{live_roomid}")
            live_room = LiveRoom(room_display_id=live_roomid,credential=c)
            for i in range(1,11): # 发送10次弹幕
                sleep_time=5+random.random()
                text=random.choice(danmu_list)
                logger.info(f"第{i}次发送弹幕，内容为：{text},等待{sleep_time:.2f}s")
                sync(live_room.send_danmaku(danmaku=Danmaku(text=text)))
                time.sleep(sleep_time)
    except:
        raise

if __name__ == "__main__":
    timer=time.perf_counter()
    c = login()
    logger.info("登录成功")
    reactivate()
    logger.info("已完成,耗时{:.2f}s".format(time.perf_counter()-timer))