import flet as ft

class ChatView(ft.Column):
    def __init__(self, my_nickname: str, peer_nickname: str, client):
        super().__init__()
        self.my_nickname = my_nickname
        self.peer_nickname = peer_nickname
        self.client = client  # guarda a instância do Client para envio P2P
        self.expand = True
        self.spacing = 5
        self.alignment = ft.MainAxisAlignment.START



        self.messages_view = ft.ListView(
            expand=True, spacing=10, auto_scroll=True,
            padding=ft.padding.symmetric(horizontal=10)
        )
        self.new_message_field = ft.TextField(
            hint_text="Digite sua mensagem...", expand=True,
            border=ft.InputBorder.UNDERLINE, border_color="#2b3b28",
            on_submit=self._send_message_click,
            autofocus=True
        )
        self.send_button = ft.IconButton(
            icon=ft.Icons.SEND_ROUNDED, icon_color=ft.Colors.BLACK, tooltip="Enviar",
            on_click=self._send_message_click
        )
        input_bar = ft.Container(
            content=ft.Row(
                [self.new_message_field, self.send_button],
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=ft.padding.symmetric(vertical=5, horizontal=10),
            border=ft.border.only(top=ft.BorderSide(1, "#2b3b28"))
        )
        name =ft.Row(
            controls=[
                ft.Text(
                    f"{self.peer_nickname}",
                    size=30, weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                )
            ],
            alignment= ft.MainAxisAlignment.CENTER,
        )
        self.controls = [name,self.messages_view, input_bar]
        self.alignment = ft.MainAxisAlignment.START
        self.horizontal_alignment = ft.CrossAxisAlignment.START


    def _add_message_to_view(self, message_text: str, from_self: bool):
        sender_name = self.my_nickname if from_self else self.peer_nickname
        alignment = ft.MainAxisAlignment.END if from_self else ft.MainAxisAlignment.START
        bubble_color = "#072b00" if from_self else "#2b3b28"
        chat_bubble_content = ft.Column(
            [
                ft.Text(message_text, selectable=True, size=15,color = ft.Colors.WHITE)
            ],
            spacing=4
        )
        bubble_container = ft.Container(
            content=chat_bubble_content,
            bgcolor=bubble_color,
            padding=12,
            border_radius=15,
            width=self.page.width * 0.7 if self.page else 400,
        )
        self.messages_view.controls.append(ft.Row([bubble_container], alignment=alignment))
        if self.page:
            self.page.update()

    def _send_message_click(self, e):
        message = self.new_message_field.value.strip()
        if not message:
            return

        # Exibe a mensagem localmente
        self._add_message_to_view(message, from_self=True)
        self.new_message_field.value = ""
        self.new_message_field.focus()
        self.page.update()

        # Envia a mensagem via Client para o peer (IP e porta devem ser obtidos via client.get_user)
        success, user_info = self.client.get_user(self.peer_nickname)
        if success:
            addr = user_info["addr"][0] if isinstance(user_info["addr"], (list, tuple)) else user_info["addr"]
            port_p2p = user_info["port_p2p"]
            sent = self.client.send_p2p(addr, port_p2p, message)
            if not sent:
                # Opcional: mostrar erro ou notificação que não enviou
                print(f"Erro ao enviar mensagem para {self.peer_nickname}")
        else:
            self.page.snack_bar.content = ft.Text("O usuário não está online.")
            self.page.snack_bar.open = True
            self.page.update()


    def add_message(self, sender: str, message: str):
        self._add_message_to_view(message, from_self=(sender == self.my_nickname))
