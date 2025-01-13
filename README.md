# 飞机大战游戏

一个使用 Pygame 开发的经典飞机大战游戏。

## 游戏特点

- 美观的游戏界面
- 流畅的游戏体验
- 计分系统
- 生命值系统

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行游戏

```bash
python plane_war.py
```

## 游戏控制

- 左右方向键：控制飞机左右移动
- 空格键：发射子弹
- ESC：退出游戏

## 游戏规则

1. 使用方向键控制飞机躲避敌机
2. 使用空格键发射子弹击落敌机
3. 每击落一个敌机得10分
4. 被敌机撞击会减少生命值
5. 生命值耗尽游戏结束

## 文件结构

```
.
├── plane_war.py    # 游戏主程序
├── requirements.txt # 项目依赖
├── README.md       # 说明文档
└── assets/         # 游戏资源
    ├── player.png  # 玩家飞机图片
    ├── enemy.png   # 敌机图片
    ├── bullet.png  # 子弹图片
    └── background.png # 背景图片
``` 