import _io
import argparse
import os
import socket
import struct
import sys
import time
from pathlib import Path
import threading
from settings import *
from utils import *
import psutil

BASE_PATH = ''


server_info = {
    'max_block_size': 8192,
    'users_num': 0,
}

MAX_BUFF_SIZE = 512

"""定时更新max_block_size，防止内存耗尽
"""


def update_server_info():
    while True:
        time.sleep(3)
        available_memory = psutil.virtual_memory().available
        print_time("Available memory: %s bytes" % available_memory)
        while server_info['max_block_size'] * server_info['users_num'] > 0.8 * available_memory:
            server_info['max_block_size'] = int(server_info['max_block_size'] / 2)
            print_time("max block size changed to %d" % server_info['max_block_size'])


"""获取block_size
"""


def get_block_size():
    assert 'max_block_size' in server_info.keys()
    return server_info['max_block_size']


"""处理下载
"""


def handle_conversation(client, _file, file_path):
    # 允许下载，返回文件大小
    client.send_ack_packet(tag=FILE_INFO_TAG, file=_file)
    print_time("Client download started: %s" % file_path)
    # 打开文件
    _file = _file.open("rb")
    # 传输数据
    client.download(_file, get_block_size())
    client.close()
    print_time("Client download finished: %s" % file_path)
    server_info['users_num'] -= 1


class Server:
    def __init__(self, interface="127.0.0.1", port=12312, fd=5):
        self.socket = create_socket(interface, port, fd)

    """获取一个客户请求
    """
    def get_client(self):
        # 用户数加1
        server_info['users_num'] += 1
        try:
            sock, addr = self.socket.accept()
            client = Socket(sock, MAX_BUFF_SIZE)
            print_time("%s:%s connected" % (addr[0], addr[1]))
        except socket.error:
            print_time("Accept error.")
            return None, None, None
        # 获取客户端发送路径
        file_path = client.get_file_path(BASE_PATH)
        # 出错
        if not file_path:
            client.send_error_packet(INVALID_REQUEST)
            return None, None, None
        _file = Path(file_path)
        # 找到该文件
        if _file.is_file():
            return client, _file, file_path
        else:
            # 文件不存在
            print_time("File not found: %s" % file_path)
            client.send_error_packet(FILE_NOT_FOUND, close=True)
            server_info['users_num'] -= 1
            return None, None, None

    """单线程
    """
    def single_threading_handle_conversation(self):
        while True:
            client, _file, file_path = self.get_client()
            if client:
                handle_conversation(client, _file, file_path)

    """多线程
    """
    def multi_threading_handle_conversation(self):
        while True:
            client, _file, file_path = self.get_client()
            if client:
                t = threading.Thread(
                    target=handle_conversation,
                    args=(client, _file, file_path)
                )
                t.start()

    def start(self, mode):
        print_time("Server start...")
        t = threading.Thread(
            target=update_server_info,
        )
        t.start()

        # 单线程模式
        if mode == 1:
            self.single_threading_handle_conversation()
        # 多线程模式
        if mode == 2:
            self.multi_threading_handle_conversation()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Server config")
    parser.add_argument("--ip", "-i", help="ip", required=True, type=str)
    parser.add_argument("--port", "-p", help="port", required=True, type=int)
    parser.add_argument("--mode", "-m", help="mode", required=True, type=int)
    args = parser.parse_args()
    server = Server(args.ip, args.port)
    assert args.mode in (1, 2)
    try:
        server.start(args.mode)
    except KeyboardInterrupt:
        print('Interrupted')
        sys.exit(0)
