# 内网聊天室

一个基于 Python 的内网聊天应用，支持多人聊天和 AI 助手功能。

## 功能特点

- 多人实时聊天
- 消息历史记录
- AI 助手（基于 DeepSeek API）
- 美观的图形界面
- SQLite 数据存储

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置说明

1. 获取 DeepSeek API Key：
   - 访问 [DeepSeek Platform](https://platform.deepseek.com/)
   - 注册账号并创建 API Key
   - 将 API Key 替换到 `server.py` 中的 `self.api_key`

2. 配置文件说明：
   - `server.py`: 服务器端程序
   - `client.py`: 客户端程序
   - `requirements.txt`: 项目依赖
   - `chat.db`: 消息数据库（自动创建）

## 使用方法

1. 启动服务器：
```bash
python server.py
```

2. 启动客户端：
```bash
python client.py
```

3. AI 助手使用：
   - 在聊天中输入 `@bot` 加上你的问题
   - 例如：`@bot 你好`
   - AI 助手会自动回复你的问题

## 技术栈

- Python 3.x
- PyQt6（GUI）
- SQLite（数据存储）
- Socket（网络通信）
- OpenAI SDK（API 调用）
- DeepSeek API（AI 服务）

## 注意事项

1. API 使用：
   - 需要有效的 DeepSeek API Key
   - API 调用可能产生费用
   - 建议合理设置 max_tokens 限制

2. 网络要求：
   - 确保服务器能访问 DeepSeek API
   - 客户端需要能连接到服务器

## 开发计划

- [ ] 支持图片发送
- [ ] 添加用户认证
- [ ] 支持私聊功能
- [ ] 优化 AI 响应速度
- [ ] 添加更多 AI 功能 