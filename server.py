import socket
import threading
import json
import sqlite3
from datetime import datetime
import requests
from openai import OpenAI

class ChatServer:
    def __init__(self, host='0.0.0.0', port=9999):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = {}  # {client_socket: username}
        self.db_lock = threading.Lock()
        self.setup_database()
        # API 配置
        self.api_key = "sk-2a4a714760584638950c829476acced8"  # 替换为你的 API key
        self.api_url = "https://api.deepseek.com/v1/chat/completions"  # 官方 API 地址
        self.bot_name = "Bot助手"

    def setup_database(self):
        """初始化数据库"""
        with sqlite3.connect('chat.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def get_db_connection(self):
        """获取数据库连接"""
        return sqlite3.connect('chat.db')

    def start(self):
        """启动服务器"""
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"服务器启动成功，监听地址：{self.host}:{self.port}")
        
        while True:
            client_socket, address = self.server_socket.accept()
            print(f"新的连接：{address}")
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def broadcast(self, message, sender_socket=None, include_sender=False):
        """广播消息给所有客户端"""
        for client_socket in self.clients:
            if client_socket != sender_socket or include_sender:
                try:
                    client_socket.send(json.dumps(message).encode())
                except:
                    self.remove_client(client_socket)

    def get_bot_response(self, user_message):
        """调用 API 获取回复"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个友好的聊天助手，请用简短友好的方式回答问题。"
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 800,
                "stream": False
            }
            
            # 使用 OpenAI 格式的 API 调用
            client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com/v1"
            )
            
            try:
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=data["messages"],
                    temperature=data["temperature"],
                    max_tokens=data["max_tokens"],
                    stream=False
                )
                return response.choices[0].message.content
            except Exception as api_err:
                print(f"OpenAI API 调用错误: {str(api_err)}")
                # 如果 OpenAI SDK 调用失败，回退到直接使用 requests
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    return response.json()['choices'][0]['message']['content']
                else:
                    error_msg = response.text if response.text else str(response.status_code)
                    print(f"API Error: Status {response.status_code}, Response: {error_msg}")
                    return f"抱歉，我遇到了一些问题（错误码：{response.status_code}），请稍后再试。"
                    
        except Exception as e:
            print(f"API调用错误: {str(e)}")
            return f"抱歉，服务出现了问题：{str(e)}"

    def handle_bot_message(self, message_content, sender):
        """处理机器人消息"""
        if message_content.startswith('@bot '):
            # 提取实际的问题内容
            question = message_content[5:].strip()
            # 获取机器人回复
            bot_response = self.get_bot_response(question)
            # 广播机器人的回复
            response_message = {
                'type': 'message',
                'sender': self.bot_name,
                'content': bot_response,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.broadcast(response_message)
            # 存储机器人的回复到数据库
            with self.db_lock:
                conn = self.get_db_connection()
                try:
                    cursor = conn.cursor()
                    cursor.execute(
                        'INSERT INTO messages (sender, content) VALUES (?, ?)',
                        (self.bot_name, bot_response)
                    )
                    conn.commit()
                finally:
                    conn.close()
            return True
        return False

    def handle_client(self, client_socket):
        """处理客户端连接"""
        try:
            # 等待客户端发送用户名
            username = json.loads(client_socket.recv(1024).decode())['username']
            self.clients[client_socket] = username
            
            # 广播新用户加入
            self.broadcast({
                'type': 'system',
                'content': f'{username} 加入了聊天室'
            })
            
            while True:
                data = client_socket.recv(1024).decode()
                if not data:
                    break
                
                message = json.loads(data)
                # 存储消息到数据库
                with self.db_lock:
                    conn = self.get_db_connection()
                    try:
                        cursor = conn.cursor()
                        cursor.execute(
                            'INSERT INTO messages (sender, content) VALUES (?, ?)',
                            (username, message['content'])
                        )
                        conn.commit()
                    finally:
                        conn.close()
                
                # 广播消息（包括发送者）
                broadcast_message = {
                    'type': 'message',
                    'sender': username,
                    'content': message['content'],
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.broadcast(broadcast_message, client_socket, include_sender=True)
                
                # 检查是否是机器人命令
                self.handle_bot_message(message['content'], username)
                
        except Exception as e:
            print(f"错误：{e}")
        finally:
            self.remove_client(client_socket)

    def remove_client(self, client_socket):
        """移除客户端连接"""
        if client_socket in self.clients:
            username = self.clients[client_socket]
            del self.clients[client_socket]
            client_socket.close()
            self.broadcast({
                'type': 'system',
                'content': f'{username} 离开了聊天室'
            })

if __name__ == '__main__':
    server = ChatServer()
    server.start() 