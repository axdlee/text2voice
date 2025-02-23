# 文本转语音工具

这是一个基于硅基流动API的文本转语音工具，提供了简单的图形用户界面，可以将文本转换为语音并播放。

## 功能特点

- 文本转语音转换
- 支持多种语音选择
- 实时音频播放控制
- 简洁的用户界面

## 安装要求

- Python 3.8+
- PyQt6
- requests
- pygame
- python-dotenv

## 安装步骤

1. 克隆项目到本地:
```bash
git clone [repository-url]
cd text2voice
```

2. 安装依赖:
```bash
pip install -r requirements.txt
```

3. 配置环境变量:
创建一个`.env`文件，并添加以下内容:
```
SILICON_API_KEY=your_api_key_here
```

## 使用说明

1. 运行程序:
```bash
python main.py
```

2. 在文本输入框中输入要转换的文本
3. 从下拉菜单选择想要使用的语音
4. 点击"转换为语音"按钮
5. 转换完成后可以使用播放控制按钮播放或停止

## 注意事项

- 请确保已正确设置API密钥
- 音频文件会临时保存在`temp`目录下
- 程序退出时会自动清理临时文件

## 许可证

MIT License 