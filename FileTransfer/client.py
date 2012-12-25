import argparse
import socket
import struct
import sys
import threading
import time
import timeit

from progressbar import ProgressBar
from settings import *
import zlib

# 根目录
BASE_PATH = ''

MAX_BUFF_SIZE = 4096

"""写入文件
参数：data 二进制数据
      f    文件
"""


def write_to_file(data, f):
    f.write(data)


"""计算传输速度
参数 size 传输字节数
     elapsed 消耗时间
"""


def cal_speed(size, elapsed):
    count = 0
    d = ['B/s', 'KB/s', 'MB/s', 'GB/s', 'TB/s']
    try:
        speed = size / elapsed
        while speed > 1024:
            speed /= 1024
            count += 1
            if count >= 4:
                break
    except ZeroDivisionError:
        return '0 B/s'
    except ValueError:
        return '0 B/s'
    return ' '.join(["%0.2f" % speed, d[count]])


class Client:

    def __init__(self):
        # 套接字
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 进度条
        self.progressbar = None
        # 总接收数据大小
        self.total_recv_size = 0
        # 接收文件的大小
        self.st_size = 0

    """定时更新进度条
    """

    def update_progressbar(self):
        while True:
            time.sleep(1)
            try:
                progress = self.total_recv_size * 100 / self.st_size
                if progress >= 80:
                    self.progressbar.finish()
                    break
                if progress > self.progressbar.percent:
                    self.progressbar.update(progress)
            except ZeroDivisionError:
                pass
            except ValueError:
                break

    """与服务器建立连接
    参数 server_ip 服务器ip
         server_port 服务器端口
    """

    def connect(self, server_ip, server_port):
        self.socket.connect((server_ip, server_port))

    """接收length大小的数据
    参数 length 数据大小
    """

    def recv_all(self, length):
        blocks = []
        while length != 0:
            block = self.socket.recv(length)
            if not block:
                raise EOFError("socket closed with %d bytes left in this block" % length)
                # 进度
            block_len = len(block)
            length -= block_len
            self.total_recv_size += block_len
            blocks.append(block)
        return b''.join(blocks)

    """接收服务器一次发送的数据
    参数 compress 服务器是否压缩过数据
    """

    def get_block(self, compress=True):
        # 数据块大小
        recv_data = self.recv_all(4)
        block_length = struct.unpack("!I", recv_data)[0]
        # 结束传输
        if block_length == 0:
            return block_length, None
        else:
            block = self.recv_all(block_length)
            # 解压缩
            if compress:
                block = zlib.decompress(block)
            return block_length, block

    """下载进程
    参数 file_path 文件写入路径
    """

    def download(self, file_path, out):
        # 确保路径为字符串类型
        assert isinstance(file_path, str)
        # 编码
        path = file_path.encode(ENCODING_METHOD)
        # 封装
        pkt = struct.pack("!HH%ds" % len(path), RRQ, len(path), path)
        if len(pkt) < 512:
            pkt += (512 - len(pkt))*b'0'
        # 发出请求
        self.socket.sendall(pkt)
        try:
            # 模拟客户端异常出错
            # raise Exception('test')

            # 收到回应
            recv_pkt = self.socket.recv(MAX_BUFF_SIZE)
            # 操作码
            op = struct.unpack("!H", recv_pkt[:2])[0]
            # 服务器同意该请求
            if op == ACK:
                # 进度条线程
                self.progressbar = ProgressBar()
                self.progressbar.start()
                t = threading.Thread(target=self.update_progressbar)
                t.start()

                # 打印文件信息
                self.st_size = struct.unpack("!Q", recv_pkt[2:])[0]
                start = time.time()
                print("File(%s, size=%d Bytes) download started..." % (file_path, self.st_size))
                # 关闭写入，只接收
                self.socket.shutdown(socket.SHUT_WR)
                # 写入文件绝对路径
                path = ''.join([BASE_PATH, out])
                with open(path, 'wb') as f:
                    try:
                        while True:
                            block_size, block = self.get_block()
                            # 没有更多数据了
                            if not block:
                                self.progressbar.finish()
                                break
                            # 写入数据
                            write_to_file(block, f)
                            speed = cal_speed(self.st_size, time.time() - start)
                        print(time.time() - start)
                        print("File(%s, size=%d) download finished...%s" % (file_path, self.st_size, speed))
                    except KeyboardInterrupt:
                        sys.exit()
                    

            # 服务器拒绝该请求
            elif op == ERROR:
                errno = struct.unpack("!H", recv_pkt[2:4])[0]
                print(errno)
            else:
                print(op)
            # 释放相关资源
            self.socket.close()

        # except Exception as e:
        except socket.error as e:
            print(e)
            self.socket.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Server config")
    parser.add_argument("--ip", "-i", help="server ip", required=True, type=str)
    parser.add_argument("--port", "-p", help="server port", required=True, type=int)
    parser.add_argument("--file", "-f", help="file path", required=True, type=str)
    parser.add_argument("--out", "-o", help="output file", required=True, type=str)

    args = parser.parse_args()
    client = Client()
    client.connect(args.ip, args.port)
    client.download(args.file, args.out)
