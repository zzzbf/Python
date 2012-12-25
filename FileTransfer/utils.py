import _io
import socket
import struct
import time
from pathlib import Path
import zlib
from settings import *

""" 创建一个套接字并监听
参数：interface 监听地址
      port      监听端口
      fd        文件描述符
如果成功创建，则返回套接字，否则返回None
"""


def create_socket(interface, port, fd):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((interface, port))
        sock.listen(fd)
        return sock
    # 创建失败
    except socket.error:
        return None


"""打印时间
参数：msg 追加打印的字符串，默认为空字符串
      e   字符串结尾字符，默认为换行符
打印格式：[yyyy-mm-dd] msg
"""


def print_time(msg="", e="\n"):
    t = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    print("[%s] %s" % (t, msg), end=e)


"""获取文件信息并封装成包
参数：_file Path类型的文件
包格式：文件大小(8个字节，64位)
"""


def get_file_info_pkt(_file):
    try:
        assert isinstance(_file, Path)
    except AssertionError:
        return None
    st_size = _file.stat().st_size
    pkt = struct.pack("!Q", st_size)
    return pkt


"""Socket类，用来处理客户端的一系列操作
实例化参数：socket 套接字
"""


class Socket:
    def __init__(self, sock, buff_size):
        self.__socket = sock
        self.__buff_size = buff_size

    """发送ACK报文
    参数：kwargs 字典
    如果传入字典，则必须有tag键，tag用来指示ack包的类型
    """
    def send_ack_packet(self, **kwargs):
        try:
            pkt = struct.pack("!H", ACK)
            if kwargs:
                assert 'tag' in kwargs.keys()
                if kwargs['tag'] == FILE_INFO_TAG:
                    pkt += get_file_info_pkt(kwargs['file'])
            self.__socket.sendall(pkt)
        except Exception as e:
            print_time("send_ack_packet:%s" % str(e))
            self.send_error_packet(SERVER_ERROR, close=True)

    """发送ERROR报文
    参数：errno 错误码
          close 发送完是否关闭输出流
    """
    def send_error_packet(self, errno, close=False):
        try:
            assert isinstance(errno, int)
            pkt = struct.pack("!HH", ERROR, errno)
            self.__socket.sendall(pkt)
            self.close()
        except Exception as e:
            print_time("send_error_packet:%s" % str(e))
            self.close()

    """客户端下载完成，发送完成标志
    """

    def download_finished(self):
        try:
            pkt = struct.pack("!I", 0)
            self.__socket.sendall(pkt)
        except Exception as e:
            print_time("download_finished:%s" % str(e))
            self.send_error_packet(SERVER_ERROR, close=True)

    """获取客户端发送的文件路径
        参数：base_path 根目录
    """
    def get_file_path(self, base_path):
        try:
            recv_pkt = self.__socket.recv(self.__buff_size)
            # 操作码 文件路径字符串长度
            op, file_path_length = struct.unpack("!HH", recv_pkt[:4])
            # 操作吗必须为RRQ
            if op != RRQ:
                self.send_error_packet(INVALID_REQUEST, close=True)
                print_time("INVALID REQUEST")
                return None
            file_path = struct.unpack("!%ds" % file_path_length, recv_pkt[4:4+file_path_length])[0]
            file_path = file_path.decode(ENCODING_METHOD)
            file_path = ''.join([base_path, file_path]).replace('\\', '/')
            return file_path
        except Exception as e:
            print_time("get_file_path:%s" % str(e))
            self.send_error_packet(SERVER_ERROR, close=True)
            return None

    """发送一个文件数据块
    参数：data 数据
    """
    def put_block(self, data, compress):
        block_length = len(data)
        if block_length == 0:
            return False
        try:
            # 压缩
            if compress:
                data = zlib.compress(data)
                block_length = len(data)
            # 发送数据长度
            header = struct.pack("!I", block_length)
            self.__socket.sendall(header)
            # 发送数据
            pkt = struct.pack("!%ds" % block_length, data)
            self.__socket.sendall(pkt)
            return True
        except Exception as e:
            print_time("put_block:%s" % str(e))
            self.send_error_packet(SERVER_ERROR, close=True)
            return False

    """客户端下载
    参数：file Path类
          loop 事件循环
    """

    def download(self, file, block_size, compress=True):
        self.__socket.shutdown(socket.SHUT_RD)
        assert isinstance(file, _io.BufferedReader)
        try:
            while True:
                data = file.read(block_size)
                if not self.put_block(data, compress):
                    break
                del data
            self.download_finished()
            file.close()
            return True
        except Exception as e:
            print_time("download:%s" % str(e))
            self.send_error_packet(SERVER_ERROR, close=True)
            file.close()
            return False

    """清理系统资源
    """
    def close(self):
        try:
            self.__socket.close()
            addr, port = self.__socket.getsockname()
            print_time("Connection closed.(%s:%s)" % (addr, port))
        except socket.error:
            pass
        except Exception as e:
            print_time(str(e))
