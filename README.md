# 文本转语音工具 (Text-to-Speech Tool)

这是一个基于硅基流动 API 的文本转语音转换工具，提供了简洁直观的图形用户界面，支持实时文本转语音和音频播放控制。

## ✨ 功能特点

- 支持中文、英文等多语言文本转换
- 提供多种语音音色选择
- 实时音频播放控制（播放、暂停、停止）
- 简洁美观的图形用户界面
- 自动音频文件管理
- 支持长文本分段转换

## 🔧 技术栈

- Python 3.8+
- PyQt6 - GUI框架
- Requests - HTTP请求
- Pygame - 音频播放
- python-dotenv - 环境变量管理

## 📋 系统要求

- 操作系统：Windows/macOS/Linux
- Python 3.8 或更高版本
- 2GB 以上可用内存
- 网络连接（用于API调用）

## 🚀 快速开始

### 安装

1. 克隆项目到本地:
```bash
git clone https://github.com/yourusername/text2voice.git
cd text2voice
```

2. 创建并激活虚拟环境（推荐）:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. 安装依赖:
```bash
pip install -r requirements.txt
```

### 配置

1. 在项目根目录创建 `.env` 文件
2. 添加以下配置:
```plaintext
SILICON_API_KEY=your_api_key_here
```

### 运行

```bash
python main.py
```

## 💡 使用指南

1. 启动程序后，您将看到主界面
2. 点击设置, 输入 API KEY
3. 在文本输入框中输入或粘贴要转换的文本
4. 从下拉菜单中选择期望的语音音色
5. 点击"转换为语音"按钮开始转换
6. 转换完成后，使用播放控制按钮管理音频播放

## ⚙️ 高级功能

- **批量转换**: 支持长文本自动分段转换
- **音频缓存**: 自动管理已转换的音频文件
- **错误处理**: 完善的错误提示和异常处理机制
- **配置持久化**: 记住用户的偏好设置

## 📝 注意事项

- API 密钥请妥善保管，不要泄露
- 音频文件临时存储在 `temp` 目录，程序退出时会自动清理
- 建议单次转换文本长度不超过 5000 字
- 请确保网络连接稳定

## 🔍 故障排除

常见问题：

1. **API 调用失败**
   - 检查 API 密钥是否正确
   - 确认网络连接是否正常
   - 查看 API 调用限制是否超额

2. **音频播放问题**
   - 检查系统音频设备是否正常
   - 确认音频文件是否成功下载
   - 尝试重启程序

## 🤝 贡献指南

欢迎提交 Pull Request 或 Issue！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 📮 联系方式

- 项目维护者: [Sheldon Lee]
- Email: [xdlee110@gmail.com]
- 项目主页: [GitHub Repository URL]

## 🙏 致谢

- 感谢硅基流动提供的 API 支持
- 感谢所有项目贡献者

## 🔨 构建说明

### Windows 构建

1. 安装 PyInstaller:
```bash
pip install pyinstaller
```

2. 构建可执行文件:
```bash
pyinstaller --noconsole --add-data ".env;." --add-data "assets/*;assets" --icon "assets/icon.ico" --name "Text2Voice" main.py
```

3. 构建结果位于 `dist/Text2Voice` 目录下

### macOS 构建

1. 安装必要工具:
```bash
pip install pyinstaller
brew install create-dmg  # 如果需要创建 DMG 安装包
```

2. 构建应用程序:
```bash
pyinstaller --noconsole --add-data ".env:." --add-data "assets/*:assets" --icon "assets/icon.icns" --name "Text2Voice" main.py
```

3. 创建 DMG 安装包 (可选):
```bash
create-dmg \
  --volname "Text2Voice" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --icon "Text2Voice.app" 200 190 \
  --hide-extension "Text2Voice.app" \
  --app-drop-link 600 185 \
  "Text2Voice.dmg" \
  "dist/"
```

### Linux 构建

1. 安装依赖:
```bash
sudo apt-get update
sudo apt-get install python3-dev
pip install pyinstaller
```

2. 构建可执行文件:
```bash
pyinstaller --noconsole --add-data ".env:." --add-data "assets/*:assets" --icon "assets/icon.png" --name "Text2Voice" main.py
```

3. 创建 .desktop 文件 (可选):
```bash
cat > Text2Voice.desktop << EOL
[Desktop Entry]
Name=Text2Voice
Exec=/opt/Text2Voice/Text2Voice
Icon=/opt/Text2Voice/assets/icon.png
Type=Application
Categories=Utility;
EOL
```

### 构建注意事项

- 确保所有依赖都已正确安装
- 构建前请先测试程序运行正常
- 检查资源文件路径是否正确
- Windows 路径分隔符使用 `;`，Unix 系统使用 `:`
- 建议使用虚拟环境进行构建
- 确保图标文件格式正确:
  - Windows: .ico
  - macOS: .icns
  - Linux: .png

### 发布检查清单

1. 基本检查:
   - 程序能正常启动和运行
   - 所有功能正常工作
   - 资源文件完整加载
   - 配置文件正确读取

2. 系统兼容性:
   - Windows: 测试 Win10/11
   - macOS: 测试最新三个版本
   - Linux: 测试主流发行版

3. 打包内容:
   - 主程序
   - 依赖库
   - 资源文件
   - 配置文件
   - 使用说明
   - 许可证文件

## 📁 项目结构

```
text2voice/
├── assets/                # 资源文件目录
│   ├── icon.ico          # Windows 图标
│   ├── icon.icns         # macOS 图标
│   └── icon.png          # Linux 图标和源文件
├── temp/                 # 临时音频文件目录
├── main.py              # 主程序
├── api_client.py        # API 客户端
├── audio_player.py      # 音频播放器
├── requirements.txt     # 依赖清单
├── .env                 # 环境配置
└── README.md           # 项目说明 