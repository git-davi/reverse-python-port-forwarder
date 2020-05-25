#!/bin/python3

import socket
import time
import sys
import threading
import argparse


BUFFER_SIZE = 0x400
rppf_conn = None


def make_listening_server(address) :
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(address)
    server_socket.listen()

    return server_socket


# tunnel connection should be always alive and so should never launch error
# if tunnel connection drop you should restart the program
def tunnel2rppf() :
    while True :
        data = tunnel_conn.recv(BUFFER_SIZE)
        if not data :
            raise Exception("Tunnel has dropped, this shouldn't happen, restart RPPF.")
        
        try :
            rppf_conn_lock.acquire()
            rppf_conn.sendall(data)
            rppf_conn_lock.release()
        except Exception :
            raise Exception("RPPF connection has been closed")



# rppf is listening and will accept incoming connections
def rppf2tunnel() :
    global rppf_conn

    while True :
        while True :
            data = rppf_conn.recv(BUFFER_SIZE)
            if not data :
                break

            try :
                tunnel_conn.sendall(data)
            except Exception :
                raise Exception("Tunnel has dropped, this shouldn't happen, restart RPPF.")

        rppf_conn_lock.acquire()
        rppf_conn.shutdown(socket.SHUT_RDWR)
        rppf_conn.close()

        rppf_conn, address = rppf_socket.accept()
        rppf_conn_lock.release()


parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter, 
        description=
        u'''
---------------------------------------
 Python Reverse Port Forwarder (Local)
---------------------------------------
Welcome to the PRPF, a simple port forwarder written in python.
This code should be running on local (attacker) machine.
The program will be listening for the incoming tunnel connection from
remote_portfwd.py (thost:tport).
After the connection is established the PRPF is ready to forward data. 
Just send data to the service address.
---------------------------------------
* Only tcp protocol supported *

     __                          __
    |==|                        |==|
    |= |                        |= |
    |^*|  ----\u2620----\u2620----\u2620----   |^*|
    |__|                        |__|
        ''')



parser.add_argument("tunnel_address", metavar="thost:tport", type=str, help="Tunnel address to listen to")
parser.add_argument("rppf_address", metavar="rhost:rport", type=str, help="The rppf address to listen to")

args = parser.parse_args()

tunnel_hostname, tunnel_port = args.tunnel_address.split(':')
tunnel_address = (tunnel_hostname, int(tunnel_port))
rppf_hostname, rppf_port = args.rppf_address.split(':')
rppf_address = (rppf_hostname, int(rppf_port))


try :
    print("Waiting for incoming tunnel connection...")
    tunnel_socket = make_listening_server(tunnel_address)
    tunnel_conn, address  = tunnel_socket.accept()
    print("Tunnel created")

    print("Opening rppf listening service...")
    rppf_socket = make_listening_server(rppf_address)
    print("--------------------------------------------")
    print("RPPF Service opened on " + str(rppf_address))
    print("Ready to transfer data")

    # start thread for incoming and outcoming traffic
    tunnel2rppf_t = threading.Thread(target=tunnel2rppf)
    rppf2tunnel_t = threading.Thread(target=rppf2tunnel)
    tunnel2rppf_t.daemon = True
    rppf2tunnel_t.daemon = True

    # rppf lock (needed when connection get restarted)
    rppf_conn_lock = threading.Lock()

    # start threads only after connection is initiated with rppf
    rppf_conn, address = rppf_socket.accept()

    tunnel2rppf_t.start()
    rppf2tunnel_t.start()
    
    tunnel2rppf_t.join()
    rppf2tunnel_t.join()

except KeyboardInterrupt :
    # close sockets after SIGINT
    print('\nClosing connections')
    tunnel_socket.shutdown(socket.SHUT_RDWR)
    tunnel_socket.close()
    rppf_socket.shutdown(socket.SHUT_RDWR)
    rppf_socket.close()
    print('\nStopped correctly')
    sys.exit(0)

except Exception as e :
    print('An exception occurred')
    print(e)
    print('Trying to close sockets')
    tunnel_socket.shutdown(socket.SHUT_RDWR)
    tunnel_socket.close()
    rppf_socket.shutdown(socket.SHUT_RDWR)
    rppf_socket.close()
    sys.exit(1)
