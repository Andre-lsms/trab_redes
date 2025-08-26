# Chat P2P com Servidor Central (Flet + Python)

Projeto de **chat ponto-a-ponto (P2P)** com **descoberta centralizada**.  
O **servidor** mantém a lista de usuários online; as **mensagens** são trocadas **direto entre os clientes** (P2P).  
Interface feita com **Flet**.

---


## Requisitos

- **Python 3.10+** (recomendado 3.10 ou 3.11)
- **pip** atualizado
- Permitir o app no **firewall** quando solicitado

---

## Portas e Endereços (padrão)

- **Servidor:** `127.0.0.1` na **porta 2004**
- **Clientes:** conectam em `127.0.0.1:2004` (ou no IP da máquina do servidor, se em rede)

> Se mudar a porta no `servidor.py`, mude também no cliente (em `main.py`).

---

## Como baixar o projeto

Antes de rodar o código, siga os passos para clonar o repositório na sua máquina:

1. **Acesse o repositório no GitHub:**  
   [https://github.com/Andre-lsms/trab_redes](https://github.com/Andre-lsms/trab_redes)

2. **Clone o repositório via terminal:**
   ```bash
   git clone https://github.com/Andre-lsms/trab_redes.git

## Primeira Execução (mesma máquina)

1. **(Opcional) Ambiente virtual**
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate

2. **Instalar dependências**
   ````bash
   pip install -r requirements.txt

3. **Primeira execução (mesma máquina)**
   Inicie o servidor (deixe esse terminal aberto):
   ````bash
   python servidor.py

4. **Abra o(s) cliente(s) em outro(s) terminal(is):**   
   ````bash
   python main.py
   # Abra uma segunda janela/terminal e rode novamente para ter dois clientes

## Use o app:

- Faça login com apelidos diferentes (ex.: alice e bob);
- A lista Online aparece; clique no usuário para abrir a conversa;
- Envie mensagens (a entrega é P2P entre clientes).

**🧱 Tecnologias**
Python, Flet, socket, threading
Arquitetura: servidor central de presença + mensagens P2P diretas
