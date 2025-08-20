import flet as ft
from client_chat_view import ChatView
from client import Client

def main(page: ft.Page):
    page.title = "Chat com Navegação"
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.CYAN)
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.window.resizable = False
    page.window.maximizable = False
    page.window.width = 600
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(color_scheme_seed=ft.colors.WHITE)

    DUMMY_USERS = []
    client = Client(page.pubsub)
    active_chats = {}
    client.connect()
    client.start_keepalive(interval=15)
    client.start_p2p_keepalive(lambda: [
        {
            "addr": info["addr"][0] if isinstance(info["addr"], (list, tuple)) else info["addr"],
            "port_p2p": info["port_p2p"]
        }
        for info in [client.get_user(nick)[1] for nick in active_chats.keys() if client.get_user(nick)[0]]
    ], interval=30)
    def update_user_list_ui():
        users_list_view.controls.clear()
        for user in DUMMY_USERS:
            if user == page.session.get("my_nickname"):
                continue  # não mostrar a si mesmo
            if user in active_chats:
                list_tile = ft.ListTile(
                    title=ft.Text(user, weight=ft.FontWeight.BOLD, color=ft.Colors.PRIMARY),
                    leading=ft.Icon(ft.Icons.CHAT, color=ft.Colors.PRIMARY),
                    trailing=ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_color=ft.Colors.RED_400,
                        tooltip="Fechar Chat",
                        on_click=lambda e, u=user: close_chat(u)
                    ),
                    on_click=lambda e, u=user: switch_to_chat(u)
                )
            else:
                list_tile = ft.ListTile(
                    title=ft.Text(user,color = ft.Colors.WHITE),
                    leading=ft.Icon(ft.Icons.PERSON_OUTLINE,color = ft.Colors.WHITE),
                    
                    on_click=lambda e, u=user: start_chat(u)
                )
            users_list_view.controls.append(
                ft.Container(
                    content=list_tile,
                    bgcolor="#2b3b28", border_radius=8
                )
            )
        page.update()

    def close_chat(peer_nickname: str):
        index_to_remove = -1
        for i, dest in enumerate(navigation_bar.destinations):
            if dest.label == peer_nickname:
                index_to_remove = i
                break
        if index_to_remove != -1:
            navigation_bar.destinations.pop(index_to_remove)
            main_content_stack.controls.pop(index_to_remove)
            del active_chats[peer_nickname]
            navigation_bar.selected_index = 0
            switch_view(0)
            update_user_list_ui()
            page.update()

    def switch_to_chat(peer_nickname: str):
        for i, dest in enumerate(navigation_bar.destinations):
            if dest.label == peer_nickname:
                navigation_bar.selected_index = i
                switch_view(i)
                return

    def switch_view(selected_index):
        for i, view in enumerate(main_content_stack.controls):
            view.visible = (i == selected_index)
        page.update()

    def on_nav_change(e):
        switch_view(e.control.selected_index)

    def start_chat(peer_nickname: str):
        if peer_nickname in active_chats:
            switch_to_chat(peer_nickname)
            return

        chat_view = ChatView(
            my_nickname=page.session.get("my_nickname"),
            peer_nickname=peer_nickname,
            client=client  # integração: ChatView pode enviar via Client
        )
        active_chats[peer_nickname] = chat_view
        main_content_stack.controls.append(chat_view)
        navigation_bar.destinations.append(
            ft.NavigationBarDestination(
                icon=ft.Icons.CHAT_BUBBLE_OUTLINE,
                selected_icon=ft.Icons.CHAT_BUBBLE,
                label=peer_nickname
            )
        )
        new_index = len(navigation_bar.destinations) - 1
        navigation_bar.selected_index = new_index
        switch_view(new_index)
        update_user_list_ui()

    def handle_register(e):
        nickname = username_field.value.strip()
        if not nickname:
            username_field.error_text = "Insira um nome de usuário"
            page.update()
            return

        username_field.error_text = ""
        page.update()
        page.session.set("my_nickname", nickname)
        
        success, msg = client.register(nickname)
        if not success:
            username_field.error_text = msg or "Nome de usuário já em uso."
            page.update()
            return

        page.controls.clear()
        update_user_list_ui()
        page.navigation_bar = navigation_bar
        page.add(main_content_stack)
        page.title = f"Chat com Navegação - {nickname}"
        page.update()

    def on_pubsub_event(event):
        if event["type"] == "user_list":
            DUMMY_USERS.clear()
            DUMMY_USERS.extend(event["payload"])
            update_user_list_ui()

        elif event["type"] == "p2p_message":
            sender = event["from"]
            message = event["message"]

            if sender not in active_chats:
                start_chat(sender)
            active_chats[sender].add_message(sender, message)  # ChatView exibe

    page.pubsub.subscribe(on_pubsub_event)

    users_list_view = ft.ListView(expand=True, spacing=10, padding=10)
    online_view = ft.Column(
        [ft.Text("Usuários Online", size=24, weight=ft.FontWeight.BOLD,), users_list_view],
        expand=True
    )

    main_content_stack = ft.Stack(controls=[online_view], expand=True)

    navigation_bar = ft.NavigationBar(
        selected_index=0,
        on_change=on_nav_change,
        destinations=[
            ft.NavigationBarDestination(
                icon=ft.Icons.PEOPLE_OUTLINE,
                selected_icon=ft.Icons.PEOPLE,
                label="Online"
            )
        ],
        indicator_color=ft.Colors.WHITE,
    )

    username_field = ft.TextField(
        label="Insira seu nome de usuário",
        autofocus=True,
        on_submit=handle_register,
        width=300,
        border_color="#072b00",
        error_style=ft.TextStyle(color=ft.Colors.RED),
    )

    login_view = ft.Column(
        [
            ft.Text("Bem-vindo", size=32),
            username_field,
            ft.ElevatedButton(
                "Entrar",
                color=ft.Colors.WHITE,
                on_click=handle_register,
                width=300,
                height=50,
                bgcolor="#072b00",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5))
            ),
            ft.Text("Ao clicar em Entrar, você concorda em não enviar mensagens ofensivas ou ilegais. Além disso,"
                    " aceita que qualquer usuário possa iniciar chats com você, e que essas conversas só serão encerradas "
                    "quando você sair da aplicação.",width=300, size=10, color=ft.Colors.GREY),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True
    )

    page.add(login_view)

if __name__ == "__main__":
    ft.app(target=main)
