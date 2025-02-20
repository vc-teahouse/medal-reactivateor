import os
import json
from blapi_port.login_port import login_with_qrcode

def login():
    c = login_with_qrcode()
    try:
        c.raise_for_no_sessdata()
        c.raise_for_no_bili_jct()
        coco=json.dumps(c.get_cookies(),ensure_ascii=False)
    except:
        os._exit(1)
    finally:
        with open(file="./cookie.json",mode="w",encoding="utf-8",errors="ignore") as cookies:
            cookies.write(coco)
    return c

if __name__ == "__main__":
    login()