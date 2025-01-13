import sqlite3

def view_messages():
    try:
        # 连接到数据库
        conn = sqlite3.connect('chat.db')
        cursor = conn.cursor()
        
        # 查询所有消息
        cursor.execute('SELECT * FROM messages')
        messages = cursor.fetchall()
        
        # 打印消息
        print("\n=== 聊天记录 ===")
        for msg in messages:
            print(f"ID: {msg[0]}")
            print(f"发送者: {msg[1]}")
            print(f"内容: {msg[2]}")
            print(f"时间: {msg[3]}")
            print("-" * 30)
            
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    view_messages() 