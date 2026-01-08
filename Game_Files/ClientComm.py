import socket
import threading
import queue
import sys
import time
from cipher import DiffiHelman, AESCipher

# client
class ClientComm:
    def __init__(self, server_ip, port, recvQ):
        self.my_socket = socket.socket()
        self.server_ip = server_ip
        self.port = port
        self.recvQ = recvQ
        self.cipher = None
        self.open = False
        threading.Thread(target=self._mainLoop,).start()

    def _mainLoop(self):
        """
        conect to client and exhcange keys and recv messages
        :return: None
        """
        try:
            self.my_socket.connect((self.server_ip, self.port))
        except Exception as e:
            print("error in connect:", e)
            sys.exit("server is down - try later")

        self._exchange_key()
        if not self.cipher:
            sys.exit("couldn't exchange keys")
        self.open = True
        while True:
            if self.open:
                decrypt_msg = ""
                try:
                    length = self.my_socket.recv(8).decode()
                    if length:
                        msg = self.my_socket.recv(int(length))
                        decrypt_msg = self.cipher.decrypt(msg)
                except Exception as e:
                    print(f"error in receiving message here - {e}")
                    self._close_client()
                    continue
                if decrypt_msg:
                    self.recvQ.put(decrypt_msg)

    def _close_client(self):
        """
        close the connection
        :return: None
        """
        try:
            self.my_socket.close()
            print("Client connection closed.")
        except Exception as e:
            print(f"Error closing client: {e}")
        self.open = False

    def close_client(self):
        """
        close the connection
        :return: None
        """
        self._close_client()

    def client_exchange(self, diffie, socket):
        """
        exchange keys with server according to protocol
        :param diffie: diffie helman object
        :param socket: socket
        :return: shared key as string
        """
        server_public_key = None
        ret = None
        try:
            server_public_key = int(socket.recv(5).decode())
            socket.send(str(diffie.public_key).zfill(5).encode())
        except Exception as e:
            print(f"Error in receiving/sending public key: {e}")
        if server_public_key:
            shared_key = pow(server_public_key, diffie.private_key, diffie.p)
            ret = str(shared_key)
        return ret

    def _exchange_key(self):
        """
        Exchange key with server
        :return: if exchanged
        """
        diffie = DiffiHelman()
        shared_key = self.client_exchange(diffie, self.my_socket)
        flag = False
        if shared_key:
            self.cipher = AESCipher(shared_key)
            print(f"Shared key established with server - {shared_key}")
            flag = True
        return flag

    def send_msg(self, msg):
        """
        send message to server
        :param msg:
        :return:
        """
        flag = False
        if self.cipher and self.open:
            msg = self.cipher.encrypt(msg)
            if len(msg) > 0:
                try:
                    self.my_socket.send(str(len(msg)).zfill(8).encode())
                    self.my_socket.send(msg)
                    flag = True
                except Exception as e:
                    print(f"error in sending message - {e}")
                    self._close_client()
                    self.open = False
        return flag

if __name__ == "__main__":
    msgsQ = queue.Queue()
    # Create the server and client
    myClient = ClientComm("127.0.0.1", 1234, msgsQ)
    time.sleep(0.2)
    myClient.send_msg("hello server")
    print(msgsQ.get())







