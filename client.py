import socket
import json
import threading
import  time

class Client:
    def __init__(self, pubsub, host="127.0.0.1", port=2004, port_p2p=None):
        self.user = None
        self.host = host
        self.port = port
        self.port_p2p = port_p2p or self._get_random_port()
        self.connection = None
        self.response_data = None
        self.response_event = threading.Event()
        self.pubsub = pubsub
        self.stop_event = threading.Event()

    def _get_random_port(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("0.0.0.0", 0))  # porta aleatória
        port = s.getsockname()[1]
        s.close()
        return port

    def connect(self):
        try:
            self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connection.connect((self.host, self.port))
            threading.Thread(target=self.listen_server, daemon=True).start()
            threading.Thread(target=self.listen_p2p, daemon=True).start()
            return True
        except Exception as e:
            print(f"Erro ao conectar: {e}")
            return False

    def listen_server(self):
        while not self.stop_event.is_set():
            try:
                response = self.connection.recv(1024)
                if not response:
                    break
                response_json = json.loads(response.decode("utf-8"))
                action = response_json.get("action")
                data = response_json.get("data", {})

                if action in ("register_response", "get_user_response"):
                    self.response_data = data
                    self.response_event.set()
                elif action == "online_list_update":
                    print("Lista recebida do servidor")
                    users_list = data.get("users", [])
                    self.pubsub.send_all({"type": "user_list", "payload": users_list})

            except (ConnectionResetError, json.JSONDecodeError, OSError) as e:
                print(f"Conexão perdida com servidor. {e}")
                break
            except json.JSONDecodeError:
                print("ERRO: Resposta inválida do servidor. Tentando novamente...")
            except Exception as e:
                print(f"Erro inesperado no listener servidor: {e}")
                break

    def listen_p2p(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("0.0.0.0", self.port_p2p))
        s.listen()
        print(f"P2P ouvindo na porta {self.port_p2p}...")
        while not self.stop_event.is_set():
            try:
                conn, addr = s.accept()
                data = conn.recv(1024).decode("utf-8")
                if data:
                    try:
                        msg_json = json.loads(data)

                        sender = msg_json.get("from")
                        message = msg_json.get("message")
                        if message == "__ping__":
                            conn.close()
                            continue  # ignora pings
                    except Exception:
                        # fallback para mensagens antigas (texto puro)
                        sender = str(addr)
                        message = data
                    self.pubsub.send_all({"type": "p2p_message", "from": sender, "message": message})
                conn.close()
            except Exception as e:
                print(f"Erro no listener P2P: {e}")
                # Envia evento para fechar chat do peer desconectado
                self.pubsub.send_all({"type": "p2p_disconnect", "peer": str(addr[0])})


    def register(self, user):
        self.user = user
        try:
            msg = {
                "action": "register",
                "data": {"user": self.user, "port_p2p": self.port_p2p}
            }
            self.response_event.clear()
            self.connection.sendall(json.dumps(msg).encode("utf-8"))
            
            if not self.response_event.wait(timeout=5):
                return False, "O servidor não respondeu a tempo."

            response_json = self.response_data
            return (response_json.get("status") == "ok", response_json.get("msg"))
        except Exception as e:
            return False, f"Erro inesperado no cliente: {e}"

    def get_user(self, user_to_find):
        self.response_event.clear()
        msg = {"action": "get_user", "data": {"user": user_to_find}}
        self.connection.sendall(json.dumps(msg).encode("utf-8"))

        if not self.response_event.wait(timeout=5):
            return False, "O servidor não respondeu a tempo."

        response_data = self.response_data
        if response_data.get("status") == "ok":
            return True, {
                "user": response_data.get("user"),
                "addr": response_data.get("addr"),
                "port_p2p": response_data.get("port_p2p")
            }
        else:
            return False, response_data.get("msg", "Erro desconhecido no servidor.")

    def get_online(self):
        msg = {"action": "get_online"}
        self.connection.sendall(json.dumps(msg).encode("utf-8"))

    def send_p2p(self, addr, port, message):
        """Envia mensagem diretamente para outro cliente."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((addr, port))
            msg = json.dumps({"from": self.user, "message": message})
            s.sendall(msg.encode("utf-8"))
            s.close()
            return True
        except Exception as e:
            print(f"Erro ao enviar P2P: {e}")
            return False

    def send_server(self, action, data):
        message = {"action": action, "data": data}
        self.connection.sendall(json.dumps(message).encode("utf-8"))

    def close(self):
        self.stop_event.set()
        if self.connection:
            self.connection.close()

    def start_keepalive(self, interval=30):
        def keepalive_server():
            while not self.stop_event.is_set():
                try:
                    self.send_server("ping", {})
                except Exception as e:
                    print(f"Erro no keepalive servidor: {e}")
                time.sleep(interval)
        threading.Thread(target=keepalive_server, daemon=True).start()

    def start_p2p_keepalive(self, get_peers_func, interval=30):
        def keepalive_p2p():
            while not self.stop_event.is_set():
                peers = get_peers_func()
                for peer in peers:
                    try:
                        self.send_p2p(peer["addr"], peer["port_p2p"], "__ping__")
                    except Exception as e:
                        print(f"Erro no P2P keepalive: {e}")
                time.sleep(interval)
        threading.Thread(target=keepalive_p2p, daemon=True).start()