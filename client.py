import sys
import json
import socket
import threading
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QPushButton, QTextEdit, QLineEdit,
                            QLabel, QMessageBox, QInputDialog, QScrollArea,
                            QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QSize
from PyQt6.QtGui import QPalette, QColor, QFont

class MessageBubble(QFrame):
    def __init__(self, message, timestamp, is_self=False, is_system=False, sender=None, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame {
                border: none;
                background-color: transparent;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 5, 15, 5)
        layout.setSpacing(8)
        
        if is_system:
            # 系统消息样式
            msg_label = QLabel(message)
            msg_label.setStyleSheet("""
                QLabel {
                    color: #888888;
                    padding: 5px 10px;
                }
            """)
            msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addStretch()
            layout.addWidget(msg_label)
            layout.addStretch()
        else:
            # 用户头像（可以用圆形标签代替）
            avatar = QLabel()
            avatar.setFixedSize(36, 36)
            avatar.setStyleSheet(f"""
                QLabel {{
                    background-color: {'#07C160' if is_self else '#8B8B8B'};
                    border-radius: 18px;
                    color: white;
                    font-weight: bold;
                }}
            """)
            avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
            avatar_text = '我' if is_self else (sender[0] if sender else '他')
            avatar.setText(avatar_text)
            
            # 消息容器（包含用户名、消息气泡和时间）
            msg_container = QWidget()
            msg_container_layout = QVBoxLayout(msg_container)
            msg_container_layout.setContentsMargins(0, 0, 0, 0)
            msg_container_layout.setSpacing(2)
            
            # 用户名标签
            if not is_self and sender:
                name_label = QLabel(sender)
                name_label.setStyleSheet("color: #888888; font-size: 9pt;")
                msg_container_layout.addWidget(name_label)
            
            # 消息气泡
            bubble = QFrame()
            bubble.setStyleSheet(f"""
                QFrame {{
                    background-color: {'#95EC69' if is_self else '#FFFFFF'};
                    border-radius: 4px;
                    padding: 2px;
                }}
            """)
            
            bubble_layout = QVBoxLayout(bubble)
            bubble_layout.setContentsMargins(4, 4, 4, 4)
            bubble_layout.setSpacing(6)
            
            # 消息内容
            msg_label = QLabel(message)
            msg_label.setWordWrap(True)
            msg_label.setStyleSheet("""
                QLabel {
                    color: #000000;
                    font-size: 10pt;
                }
            """)
            msg_label.setFont(QFont("Microsoft YaHei"))
            # msg_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)  # 允许文本选择
            
            # 设置最大宽度
            msg_label.setMaximumWidth(self.width())  # 根据窗口宽度动态设置最大宽度
            bubble_layout.addWidget(msg_label)
            msg_container_layout.addWidget(bubble)
            
            # 时间戳（在气泡下方）
            if timestamp:
                time_label = QLabel(timestamp)
                time_label.setStyleSheet("""
                    QLabel {
                        color: #888888;
                        font-size: 7pt;
                        margin-top: 2px;
                    }
                """)
                time_label.setAlignment(Qt.AlignmentFlag.AlignRight if is_self else Qt.AlignmentFlag.AlignLeft)
                msg_container_layout.addWidget(time_label)
            
            if is_self:
                layout.addStretch()
                layout.addWidget(msg_container)
                layout.addWidget(avatar)
            else:
                layout.addWidget(avatar)
                layout.addWidget(msg_container)
                layout.addStretch()
        
        self.setLayout(layout)

class ChatArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #F5F5F5;
            }
        """)
        
        self.container = QWidget()
        self.container.setStyleSheet("background-color: #F5F5F5;")
        self.layout = QVBoxLayout(self.container)
        self.layout.addStretch()
        self.setWidget(self.container)

    def add_message(self, message, timestamp, is_self=False, is_system=False, sender=None):
        bubble = MessageBubble(message, timestamp, is_self, is_system, sender)
        self.layout.insertWidget(self.layout.count() - 1, bubble)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

class SignalHandler(QObject):
    message_received = pyqtSignal(str, str, str, str)  # type, sender, content, timestamp
    
class ChatClient(QMainWindow):
    def __init__(self):
        super().__init__()
        self.socket = None
        self.username = None
        self.signal_handler = SignalHandler()
        self.signal_handler.message_received.connect(self.handle_message)
        self.init_ui()
        self.connect_to_server()

    def init_ui(self):
        """初始化UI界面"""
        self.setWindowTitle('内网聊天')  # 设置初始标题
        screen = QApplication.primaryScreen()  # 获取主屏幕
        screen_rect = screen.availableGeometry()  # 获取可用的屏幕几何形状
        x = (screen_rect.width() - 800) // 2  # 计算窗口的 x 坐标
        y = (screen_rect.height() - 600) // 2  # 计算窗口的 y 坐标
        self.setGeometry(x, y, 800, 600)  # 设置窗口位置和大小
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F5F5F5;
            }
        """)

        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # 聊天区域
        self.chat_area = ChatArea()
        layout.addWidget(self.chat_area)

        # 输入区域
        input_container = QWidget()
        input_container.setStyleSheet("""
            QWidget {
                background-color: #F5F5F5;
                border-top: 1px solid #E0E0E0;
            }
        """)
        input_container.setFixedHeight(80)  # 固定输入区域高度
        
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(10, 10, 10, 10)
        
        self.message_input = QTextEdit()
        self.message_input.setFixedHeight(60)
        self.message_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                background-color: white;
                padding: 8px;
            }
        """)
        self.message_input.setFont(QFont("Microsoft YaHei", 10))
        
        send_button = QPushButton('发送')
        send_button.setFixedSize(60, 30)
        send_button.setStyleSheet("""
            QPushButton {
                background-color: #07C160;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #06AE56;
            }
            QPushButton:pressed {
                background-color: #059B4C;
            }
        """)
        
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(send_button)
        layout.addWidget(input_container)

        # 连接信号
        send_button.clicked.connect(self.send_message)
        self.message_input.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj is self.message_input and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.NoModifier:
                self.send_message()
                return True
            if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                self.message_input.insertPlainText('\n')
                return True
        return super().eventFilter(obj, event)

    def connect_to_server(self):
        """连接到服务器"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect(('localhost', 9999))
            
            # 获取用户名
            username, ok = QInputDialog.getText(
                self, '登录', '请输入用户名:',
                QLineEdit.EchoMode.Normal, ''
            )
            if ok and username:
                self.username = username
                self.setWindowTitle(f'内网聊天 - {username}')  # 登录后更新窗口标题
                # 发送用户名到服务器
                self.socket.send(json.dumps({'username': username}).encode())
                # 启动接收消息的线程
                threading.Thread(target=self.receive_messages, daemon=True).start()
            else:
                self.close()
                
        except Exception as e:
            QMessageBox.critical(self, '错误', f'无法连接到服务器: {str(e)}')
            self.close()

    def send_message(self):
        """发送消息"""
        message = self.message_input.toPlainText().strip()
        if message:
            try:
                self.socket.send(json.dumps({
                    'type': 'message',
                    'content': message
                }).encode())
                self.message_input.clear()
            except:
                QMessageBox.warning(self, '错误', '发送消息失败')

    def receive_messages(self):
        """接收消息"""
        while True:
            try:
                data = self.socket.recv(1024).decode()
                if not data:
                    break
                message = json.loads(data)
                self.signal_handler.message_received.emit(
                    message.get('type', 'message'),
                    message.get('sender', ''),
                    message.get('content', ''),
                    message.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                )
            except:
                break
        self.socket.close()
        self.signal_handler.message_received.emit('system', '', '已断开与服务器的连接', '')

    def handle_message(self, msg_type, sender, content, timestamp):
        """处理接收到的消息"""
        if msg_type == 'system':
            self.chat_area.add_message(content, '', is_system=True)
        else:
            is_self = sender == self.username
            self.chat_area.add_message(content, timestamp, is_self=is_self, sender=sender)

    def closeEvent(self, event):
        """关闭窗口时的处理"""
        if self.socket:
            self.socket.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    client = ChatClient()
    client.show()
    sys.exit(app.exec()) 