#!/usr/bin/env python3.6

""" 
A UDP to TCP relay for use with QLabs OSC / Network cue. Forwards commands over TCP connection and allows for
arbitrary hex commands using '\b' as prefix. Host addresses go in addr_list.txt same folder as script v32
richard at thelimen dot com
"""

from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM
import threading
import _thread
from queue import Queue
import binascii

threading.stack_size(32768)


def readfile(file_path):

    with open(file_path, 'r') as f:
                        for line in f:
                            if not line.isspace():
                                addr, port = line.split(', ', maxsplit=1)
                                yield (addr, int(port))


def listen(message_q, udp_port, target_ip):

    try:
        udp_sock = socket(AF_INET, SOCK_DGRAM)
        udp_sock.bind(('', udp_port))

        print(f'local UDP port {udp_port} relays to TCP host at {target_ip}')

    except OSError as thread_error:
        print(f'Problem starting thread {_thread.get_ident()} {thread_error}')

        _thread.interrupt_main()

    else:

        while True:
                    msg, sender = udp_sock.recvfrom(64)

                    if not msg.startswith(b'\\b'):
                        print(f'Got ascii: {msg} for {target_ip}')

                    else:
                        msg = msg.lstrip(b'\\b')
                        print(f'Got hex: {msg} for {target_ip}')

                        try:
                            msg = binascii.unhexlify(msg)

                        except ValueError as err:
                            print(f'Check the hex codes: {err}')
                            continue

                    message_q.put((msg, target_ip))


def tcp_relay(message_q):

    _count = 0

    while True:
            msg, target_ip = message_q.get()

            with socket(AF_INET, SOCK_STREAM) as tcp_sock:

                try:
                    tcp_sock.settimeout(1)
                    tcp_sock.connect(target_ip)

                    reply = tcp_sock.recvfrom(512)
                    print(f'Host says: {reply}')
                    _count += 1

                except OSError as error:
                    _count += 1
                    print(f'Unable to connect to host at {target_ip} ({_count}): {error}')
                    continue

                else:
                    msg = bytearray(msg)
                    msg.append(10)

                    tcp_sock.sendall(msg)
                    print(f'Sent {msg} ({_count}) to host at {target_ip}')
                    reply = tcp_sock.recvfrom(128)
                    print(f'Host says: {reply}')


def do_setup(udp_port):

    q = Queue()

    try:

        device_list = list(readfile('addr_list.txt'))                     # get device addresses from file
        print(f'got device addresses:\n{device_list}')

    except ValueError as err:
        print(f'Something odd about the config file: \n{err}\nExiting...')
        exit(1)

    else:

        thread_count = len(device_list)
        threads = []
        udp_port_list = []

        for i in range(thread_count):

            udp_port_list.append(int(udp_port + i))

            threads.append(threading.Thread(target=listen,
                                            args=(q, udp_port_list[i], device_list[i]),
                                            daemon=True))
        for t in threads:
            t.start()

        tcp_relay(q)


if __name__ == '__main__':

    UDP_PORT = 51000           # port number of first thread
    do_setup(UDP_PORT)
