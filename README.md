# ReverseProxyPortForwarder

*linux and windows binaries available*

## Summary

This tool comes with 2 programs that must cooperate :
- **local_portfwd**
- **remote_portfwd**

These must be running on remote and local machine and are creating a tunnel for tcp packets.  
The ***local port forward*** program should be running on your local machine, after being started
it will be listening for the incoming tunnel connection handshake and will open a service port.  
I've choosen a reverse connection logic (remote -> local) instead of a simple bind beacause
it's better to escape firewall rules.  
Once the connection is established you are ready to forward packets to the remote machine 
by simply sending requests to the RPPF service address (ex. localhost:4444).  
Then the requests will be tunneled to the endpoint of the tunnel which is the ***remote port forward*** program. At last, this script is a simple proxy and it will act on behalf of you, forwarding packets to the target address (that you must specifiy during startup).
Look at bottom page for an example.

## Help menu

```shell
$ ./remote_portfwd.py -h
usage: remote_portfwd.py [-h] thost:tport fhost:fport

--------------------------------------
 Reverse Proxy Port Forwarder (Remote)
--------------------------------------
Welcome to the RPPF, a simple port forwarder written in python.
This code should be running on the remote (attacked) machine.
A tunnel will be created to the thost:tport address using a reverse 
connection logic, to bypass firewall. The data coming from the tunnel
will then be sent over a new connection to the forward address.
The tunnel address should be your RPPF local tunnel address.
Example : ./remote_portfwd.py localhost:4444 google.com:80
--------------------------------------
* Only tcp protocol supported *

     __                          __
    |==|                        |==|
    |= |                        |= |
    |^*|  ----☠----☠----☠----   |^*|
    |__|                        |__|
        

positional arguments:
  thost:tport  Your local address to be contacted
  fhost:fport  The remote address to forward to

optional arguments:
  -h, --help   show this help message and exit
```

```shell
 $ ./local_portfwd.py -h
usage: local_portfwd.py [-h] thost:tport rhost:rport

-------------------------------------
 Reverse Proxy Port Forwarder (Local)
-------------------------------------
Welcome to the RPPF, a simple port forwarder written in python.
This code should be running on local (attacker) machine.
The program will be listening for the incoming tunnel connection from
remote_portfwd.py (thost:tport).
After the connection is established the RPPF is ready to forward data. 
Just send data to the service address.
-------------------------------------
* Only tcp protocol supported *

     __                          __
    |==|                        |==|
    |= |                        |= |
    |^*|  ----☠----☠----☠----   |^*|
    |__|                        |__|
        

positional arguments:
  thost:tport  Tunnel address to listen to
  rhost:rport  The rppf address to listen to

optional arguments:
  -h, --help   show this help message and exit
```

## Simple use case