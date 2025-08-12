import socket
import threading
import json
from datetime import datetime

class Server:
    def __init__(self):
        self.IP = "127.0.0.1"
        self.PORT = 2002
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.IP, self.PORT))
        self.clients = {}
        self.clients_lock = threading.RLock()

    def start(self):
        print("\033[32m=== Iniciando o servidor ===\033[0m")
        self.server.listen()
        while True:
            conn, addr = self.server.accept()
            conn.settimeout(60)  # evita ficar preso
            threading.Thread(target=self.listen, args=(conn, addr), daemon=True).start()

    def listen(self, conn, addr):
        print(f"\033[33mNova conexão IP {addr}\033[0m")
        user = None
        try:
            while True:
                data_receive = conn.recv(1024).decode('utf-8')
                if not data_receive:
                    break

                message = json.loads(data_receive)
                action = message.get("action")
                data = message.get('data', {})

                if action == "register":
                    user = data.get("user")
                    port_p2p = data.get("port_p2p")
                    self.register(conn, addr, user, port_p2p)

                elif action == "get_user":
                    user_request = data.get("user")
                    with self.clients_lock:
                        user_data = self.clients.get(user_request)

                    if user_data:
                        user_addr = user_data['addr']
                        port_p2p = user_data['port_p2p']
                        msg = {

                            "action": "get_user_response",
                            "data": {
                                "status": "ok",
                                "user": user_request,
                                "addr": user_addr,
                                "port_p2p": port_p2p
                            }
                        }
                    else:
                        msg = {
                            "action": "get_user_response",
                            "data": {"status": "error", "msg": "Usuário não encontrado!"}
                        }
                    conn.send(json.dumps(msg).encode("utf-8"))
                elif action == "ping":
                    print("ping recebido usuario:", user)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, socket.timeout):
            print(f"Conexão com \033[31m{user or addr}\033[0m foi perdida.")
        except json.JSONDecodeError:
            print(f"ERRO: {user or addr} enviou dados inválidos. Desconectando.")
        except Exception as e:
            print(f"ERRO INESPERADO com {user or addr}: {e}")
        finally:
            with self.clients_lock:
                if user and user in self.clients:
                    del self.clients[user]
                    print(f"\033[31mUsuário '{user}' saiu\033[0m")
                    self.online_broadcast()
            conn.close()

    def online_broadcast(self):
        with self.clients_lock:
            online_users_list = list(self.clients.keys())
            print(f"\033[30;47mBROADCAST: {online_users_list}\033[31;40m [{datetime.now().strftime('%H:%M:%S')}]\033[0m")

            reply = {
                "action": "online_list_update",
                "data": {"users": online_users_list}
            }
            message_to_send = json.dumps(reply).encode("utf-8")
            for user_data in list(self.clients.values()):
                try:
                    user_data['conn'].send(message_to_send)
                except Exception as e:
                    print(f"BROADCAST: Erro ao enviar para um cliente: {e}")

    def register(self, conn, addr, user, port_p2p):
        with self.clients_lock:
            if user in self.clients:
                reply = {"action": "register_response", "data": {"status": "error", "msg": "Usuário em uso."}}
                print(f"Usuário {user} já existe")
            else:
                self.clients[user] = {'addr': addr, 'conn': conn, 'port_p2p': port_p2p}
                reply = {"action": "register_response", "data": {"status": "ok", "msg": f"Usuário '{user}' registrado."}}
                print(f"\033[33mUsuário '{user}' cadastrado\033[0m")
                self.online_broadcast()

        conn.send(json.dumps(reply).encode("utf-8"))


if __name__ == "__main__":
    server = Server()
    server.start()
