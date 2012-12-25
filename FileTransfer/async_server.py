import argparse
import asyncio
import time
from pathlib import Path

import psutil

from async_utils import Stream, print_time
from settings import *

BASE_PATH = ''

"""事件"""
loop = asyncio.get_event_loop()

"""下载协程
参数 reader 输入流
     writer 输出流
"""


async def download(reader, writer):
    stream = Stream(reader, writer)
    # 获取文件路径
    file_path = await stream.get_file_path(BASE_PATH)
    if not file_path:
        return
    _file = Path(file_path)
    if _file.is_file():
        # 文件存在
        await stream.send_ack_packet(tag=FILE_INFO_TAG, file=_file)
        print_time("Client download started: %s" % file_path)
        # 传输数据
        await stream.download(file_path, loop)
        print_time("Client download finished: %s" % file_path)
    else:
        # 文件不存在
        print_time("File not found: %s" % file_path)
        await stream.send_error_packet(FILE_NOT_FOUND, close=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Server config")
    parser.add_argument("--ip", "-i", help="ip", required=True, type=str)
    parser.add_argument("--port", "-p", help="port", required=True, type=int)
    args = parser.parse_args()
    task = asyncio.start_server(download, args.ip, args.port, loop=loop)
    server = loop.run_until_complete(task)
    print('Server start...')
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # Close the server
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
