import socket
import threading
import queue
import select
from cipher import DiffiHelman, AESCipher

# server
class ServerComm:
    def __init__(self, port, recvQ):
        self.server_socket = socket.socket()
        self.port = port
        self.recvQ = recvQ
        # ip: [soc, AES]
        self.open_clients= {}
        # soc: ip
        self.open_clients_soc_ip = {}
        self.server_socket.bind(('0.0.0.0', self.port))
        self.server_socket.listen(4)
        threading.Thread(target=self._mainLoop,).start()

    def _mainLoop(self):
        """
        adds new clients and recv messages
        :return:
        """
        print("server listen on port:", self.port)
        while True:
            rlist, _, _ = select.select([self.server_socket] + list(self.open_clients_soc_ip.keys()), [], [], 0.01)
            for current_socket in rlist:
                if current_socket is self.server_socket:
                    client_socket, addr = self.server_socket.accept()
                    print(f"{addr[0]} connected")
                    threading.Thread(target=self._exchange_key, args=(client_socket, addr[0],)).start()
                else:
                    if current_socket in self.open_clients_soc_ip.keys():
                        decrypt_msg = ""
                        msg = ""
                        current_ip = self._find_ip_by_socket(current_socket)
                        try:
                            length = current_socket.recv(8).decode()
                            if length:
                                msg = current_socket.recv(int(length))
                            else:
                                self.close_client(current_ip)
                            if current_ip and current_ip in self.open_clients and msg:
                                decrypt_msg = self.open_clients[current_ip][1].decrypt(msg)
                        except Exception as e:
                            print(f"error in receiving message - {e}")
                            self.close_client(current_ip)
                            continue
                        if decrypt_msg:
                            self.recvQ.put([current_ip, decrypt_msg])

    def _exchange_key(self, client_soc, client_ip):
        """
        Exchange the Diffie-Hellman key with the client and establish a shared AES key.
        :param client_soc: The client's socket.
        :param client_ip: The client's IP address.
        """
        diffie = DiffiHelman()
        shared_key = self.server_exchange(diffie, client_soc)
        if shared_key:
            print(f"Shared key established with client {client_ip}: {shared_key}")
            self.open_clients[client_ip] = [client_soc, AESCipher(shared_key)]
            self.open_clients_soc_ip[client_soc] = client_ip
        else:
            print(f"Failed to establish shared key with {client_ip}")

    def server_exchange(self, diffie, socket):
        client_public_key = 0
        ret = None
        try:
            socket.send(str(diffie.public_key).zfill(5).encode())
            client_public_key = int(socket.recv(5).decode())
        except Exception as e:
            print(f"Error in sending/receiving public key: {e}")
        if client_public_key:
            shared_key = pow(client_public_key, diffie.private_key, diffie.p)
            ret = str(shared_key)
        return ret

    def close_client(self, client_ip):
        """Closes the client connection."""
        try:
            if client_ip in self.open_clients.keys():
                client_soc = self.open_clients[client_ip][0]
                del self.open_clients[client_ip]
                del self.open_clients_soc_ip[client_soc]
                client_soc.close()
                print(f"Client {client_ip} closed.")
        except Exception as e:
            print(f"Error closing client {client_ip}: {e}")

    def _find_socket_by_ip(self, client_ip):
        """
        return the matching socket for the ip
        :param client_ip: ip
        :return: client socket
        """
        if client_ip in self.open_clients.keys():
            # socket
            ret = self.open_clients[client_ip][0]
        else:
            ret = None
        return ret

    def send_msg(self, client_ip, msg):
        """

        :param client_ip:
        :param msg:
        :return:
        """
        if client_ip in self.open_clients.keys():
            soc = self._find_socket_by_ip(client_ip)
            self._send_msg(soc, msg)

    def broadcast(self, msg):
        """
        send msg to all connected users
        :param msg: string
        :return:
        """
        for ip in list(self.open_clients.keys()):
            if ip:
                self.send_msg(ip, msg)

    def _send_msg(self, client_soc, msg):
        """
        send the encrypted msg
        :param client_ip:
        :param msg:
        :return:
        """
        if client_soc in self.open_clients_soc_ip.keys():
            client_ip = self._find_ip_by_socket(client_soc)
            encrypted_msg = self.open_clients[client_ip][1].encrypt(msg)
            try:
                client_soc.send(str(len(encrypted_msg)).zfill(8).encode())  # Send message length
                client_soc.send(encrypted_msg)  # Send the encrypted message
            except Exception as e:
                print(f"error in sending message - {e}")
                self.close_client(client_ip)

    def _find_ip_by_socket(self, client_soc):
        ret = ""
        if client_soc in self.open_clients_soc_ip.keys():
            ret = self.open_clients_soc_ip[client_soc]
        return ret

if __name__ == "__main__":
    msgsQ = queue.Queue()
    # Create the server and client
    myServer = ServerComm(1234, msgsQ)
    print(msgsQ.get())
    myServer.send_msg("127.0.0.1", "hello client")
