import asyncio
import socket
import struct
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import psutil

from settings import *
from utils import *
import _io

server_info = {
    'max_block_size': 4096,
    'users_num': 0,
}

MAX_BUFF_SIZE = 512

"""获取block_size
"""


def get_block_size():
    assert 'max_block_size' in server_info.keys()
    return server_info['max_block_size']


"""Stream类，异步
实例化参数：reader 输入流
           writer 输出流
"""


class Stream:
    def __init__(self, reader, writer, buff_size=MAX_BUFF_SIZE):
        self.reader = reader
        self.writer = writer
        # 线程池
        self.io_pool_exc = ThreadPoolExecutor()
        # 地址
        self.ip, self.port = self.writer.get_extra_info('peername')
        self.buff_size = buff_size

    """清理相关系统资源
    """

    async def close(self):
        try:
            print_time("Connection closed.(%s:%s)" % (self.ip, self.port))
            self.writer.close()
        except Exception:
            pass

    """发送ACK报文
    参数：kwargs 字典
    如果传入字典，则必须有tag键，tag用来指示ack包的类型
    """

    async def send_ack_packet(self, **kwargs):
        try:
            pkt = struct.pack("!H", ACK)
            if kwargs:
                assert 'tag' in kwargs.keys()
                if kwargs['tag'] == FILE_INFO_TAG:
                    pkt += get_file_info_pkt(kwargs['file'])
            self.writer.write(pkt)
            await self.writer.drain()
        except Exception as e:
            print_time("send_ack_packet:", str(e))
            await self.send_error_packet(SERVER_ERROR, close=True)

    """发送ERROR报文
    参数：errno 错误码
          close 发送完是否关闭输出流
    """

    async def send_error_packet(self, errno, close=False):
        try:
            assert isinstance(errno, int)
            pkt = struct.pack("!HH", ERROR, errno)
            self.writer.write(pkt)
            await self.writer.drain()
            if close:
                await self.close()
        except Exception:
            await self.close()

    """获取客户端发送的文件路径
    参数：base_path 根目录
    """

    async def get_file_path(self, base_path):
        try:
            recv_pkt = await self.reader.read(self.buff_size)
            # 操作码 文件路径字符串长度
            op, file_path_length = struct.unpack("!HH", recv_pkt[:4])
            # 操作吗必须为RRQ
            if op != RRQ:
                await self.send_error_packet(INVALID_REQUEST, close=True)
                print_time("INVALID REQUEST")
                return None
            file_path = struct.unpack("!%ds" % file_path_length, recv_pkt[4:4+file_path_length])[0]
            file_path = file_path.decode(ENCODING_METHOD)
            file_path = ''.join([base_path, file_path]).replace('\\', '/')
            return file_path
        except Exception as e:
            await self.send_error_packet(SERVER_ERROR, close=True)
            print_time("send_file_path:", str(e))
        return None

    """客户端下载
    参数：file Path类
          loop 事件循环
    """

    async def download(self, file, loop, compress=True):
        # 打开文件
        file = Path(file)
        file = await loop.run_in_executor(self.io_pool_exc, file.open, "rb")
        try:
            # 发送数据
            while True:
                data = await loop.run_in_executor(self.io_pool_exc, file.read, get_block_size())
                if not await self.put_block(data, compress):
                    break
            # 发送完成
            await self.download_finished()
            return True
        except Exception as e:
            print_time("download:", str(e))
            await self.send_error_packet(SERVER_ERROR, close=True)
            return False

    """客户端下载完成，发送完成标志
    """

    async def download_finished(self):
        try:
            pkt = struct.pack("!I", 0)
            self.writer.write(pkt)
            await self.writer.drain()
        except socket.error:
            await self.send_error_packet(SERVER_ERROR, close=True)

    """发送一个文件数据块
    参数：data 数据
    """

    async def put_block(self, data, compress):
        block_length = len(data)
        if compress:
            data = zlib.compress(data)
            block_length = len(data)
        if block_length == 0:
            return False
        try:
            # 发送当前数据块大小 4个字节 因此数据块最大为2^32字节
            header = struct.pack("!I", block_length)
            self.writer.write(header)
            await self.writer.drain()
            pkt = struct.pack("!%ds" % block_length, data)
            self.writer.write(pkt)
            await self.writer.drain()
            return True
        except Exception as e:
            print_time("put_block:", str(e))
            await self.send_error_packet(SERVER_ERROR, close=True)
            return False
