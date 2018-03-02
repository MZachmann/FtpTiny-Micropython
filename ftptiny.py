# this code is from uftpserver (https://github.com/cpopp/MicroFTPServer/tree/master/uftp).
# I packed it into a class and added the threading
import socket
import network
import os
import _thread

DATA_PORT = 13333

class FtpTiny:
    '''This class creates a very tiny FTP server in a thread
        x = ftptiny.FtpTiny()
        x.start()
        x.stop()'''
    def __init__(self) :
        self.dorun = True
        self.ftpsocket = None
        self.datasocket = None
        self.dataclient = None

    def start_listen(self) :
        # the two sockets are the persistant and the pasv sockets
        # so this requires pasv
        self.ftpsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.datasocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ftpsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.datasocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.ftpsocket.bind(socket.getaddrinfo("0.0.0.0", 21)[0][4])
        self.datasocket.bind(socket.getaddrinfo("0.0.0.0", DATA_PORT)[0][4])
        self.ftpsocket.listen(1)
        self.datasocket.listen(1)
        self.datasocket.settimeout(10)
        self.dataclient = None

    def send_list_data(self, cwd, dataclient):
        for file in os.listdir(cwd):
            stat = os.stat(self.get_absolute_path(cwd, file))
            file_permissions = "drwxr-xr-x" if (stat[0] & 0o170000 == 0o040000) else "-rw-r--r--"
            file_size = stat[6]
            description = "{}    1 owner group {:>13} Jan 1  1980 {}\r\n".format(file_permissions, file_size, file)
            dataclient.sendall(description)

    def send_file_data(self, path, dataclient):
        with open(path) as file:
            chunk = file.read(128)
            while len(chunk) > 0:
                dataclient.sendall(chunk)
                chunk = file.read(128)

    def save_file_data(self, path, dataclient):
        dataclient.settimeout(.5)
        with open(path, "w") as file:
            try:
                chunk = dataclient.recv(128)
                while chunk and len(chunk) > 0:
                    file.write(chunk)
                    chunk = dataclient.recv(128)
            except Exception as ex:
                pass

    def get_absolute_path(self, cwd, payload):
        # if it doesn't start with / consider
        # it a relative path
        if not payload.startswith("/"):
            payload = cwd + "/" + payload
        # and don't leave any trailing /
        return payload.rstrip("/")

    def stop(self):
        self.dorun = False
        self.thread = 0

    def start(self):
        self.dorun = True
        tid = _thread.start_new_thread(runserver, (self, ))
        self.thread = tid

def runserver(myself):
    try:
        myself.dataclient = None
        myself.start_listen()
        while myself.dorun:
            cwd = "/"
            cl, remote_addr = myself.ftpsocket.accept()
            cl.settimeout(300)
            try:
                print("FTP connection from:", remote_addr)
                cl.sendall("220 Hello. Welcome to FtpTiny.\r\n")
                while myself.dorun:
                    data = cl.readline().decode("utf-8").replace("\r\n", "")
                    if len(data) <= 0:
                        print("Client is dead")
                        break

                    command, payload =  (data.split(" ") + [""])[:2]
                    command = command.upper()

                    print("Command={}, Payload={}".format(command, payload))

                    if command == "USER":
                        cl.sendall("230 Logged in.\r\n")
                    elif command == "SYST":
                        cl.sendall("215 ESP32 MicroPython\r\n")
                    elif command == "SYST":
                        cl.sendall("502\r\n")
                    elif command == "PWD":
                        cl.sendall('257 "{}"\r\n'.format(cwd))
                    elif command == "CWD":
                        path = myself.get_absolute_path(cwd, payload)
                        try:
                            files = os.listdir(path)
                            cwd = path
                            cl.sendall('250 Directory changed successfully\r\n')
                        except:
                            cl.sendall('550 Failed to change directory\r\n')
                    elif command == "EPSV":
                        cl.sendall('502\r\n')
                    elif command == "TYPE":
                        # probably should switch between binary and not
                        cl.sendall('200 Transfer mode set\r\n')
                    elif command == "SIZE":
                        path = myself.get_absolute_path(cwd, payload)
                        try:
                            size = os.stat(path)[6]
                            cl.sendall('213 {}\r\n'.format(size))
                        except:
                            cl.sendall('550 Could not get file size\r\n')
                    elif command == "QUIT":
                        cl.sendall('221 Bye.\r\n')
                    elif command == "PASV":
                        addr = network.WLAN().ifconfig()[0]
                        cl.sendall('227 Entering Passive Mode ({},{},{}).\r\n'.format(addr.replace('.',','), DATA_PORT>>8, DATA_PORT%256))
                        myself.dataclient, data_addr = myself.datasocket.accept()
                        print("FTP Data connection from:", data_addr)
                    elif command == "LIST":
                        try:
                            myself.send_list_data(cwd, myself.dataclient)
                            myself.dataclient.close()
                            cl.sendall("150 Here comes the directory listing.\r\n")
                            cl.sendall("226 Listed.\r\n")
                        except:
                            cl.sendall('550 Failed to list directory\r\n')
                        finally:
                            myself.dataclient.close()
                    elif command == "RETR":
                        try:
                            myself.send_file_data(myself.get_absolute_path(cwd, payload), myself.dataclient)
                            myself.dataclient.close()
                            cl.sendall("150 Opening data connection.\r\n")
                            cl.sendall("226 Transfer complete.\r\n")
                        except:
                            cl.sendall('550 Failed to send file\r\n')
                        finally:
                            myself.dataclient.close()
                    elif command == "STOR":
                        try:
                            cl.sendall("150 Ok to send data.\r\n")
                            myself.save_file_data(myself.get_absolute_path(cwd, payload), myself.dataclient)
                            myself.dataclient.close()
                            print("Finished receiving file")
                            cl.sendall("226 Transfer complete.\r\n")
                        except Exception as ex:
                            print("Failed to receive file: " + str(ex))
                            cl.sendall('550 Failed to send file\r\n')
                        finally:
                            print("Finally closing dataclient")
                            myself.dataclient.close()
                    else:
                        cl.sendall("502 Unsupported command.\r\n")
                        print("Unsupported command {} with payload {}".format(command, payload))

            finally:
                print("Finally closing socket")
                cl.close()
    finally:
        myself.datasocket.close()
        myself.ftpsocket.close()
        if myself.dataclient is not None:
            myself.dataclient.close()
