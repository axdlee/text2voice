#!/bin/bash

# 确保 assets 目录存在
mkdir -p assets

# 1. 创建基础 PNG 图标 (512x512)
cat > assets/icon.svg << EOL
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="512" height="512" viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg">
  <rect width="512" height="512" fill="#4A90E2" rx="64"/>
  <path d="M256 128c-70.7 0-128 57.3-128 128s57.3 128 128 128 128-57.3 128-128S326.7 128 256 128zm0 224c-52.9 0-96-43.1-96-96s43.1-96 96-96 96 43.1 96 96-43.1 96-96 96z" fill="white"/>
  <circle cx="256" cy="256" r="48" fill="white"/>
</svg>
EOL

# 检查是否安装了必要的工具
command -v magick >/dev/null 2>&1 || { echo "请先安装 ImageMagick"; exit 1; }

# 首先从 SVG 生成 PNG
magick convert assets/icon.svg assets/icon.png

# 创建 macOS 图标所需的不同尺寸
mkdir -p assets/icon.iconset
sizes=("16" "32" "64" "128" "256" "512")
for size in "${sizes[@]}"; do
    # 正常分辨率
    magick convert assets/icon.png -resize ${size}x${size} assets/icon.iconset/icon_${size}x${size}.png
    # 高分辨率 (@2x)
    magick convert assets/icon.png -resize $((size*2))x$((size*2)) assets/icon.iconset/icon_${size}x${size}@2x.png
done

# 为 Windows 创建 ICO 文件
magick convert assets/icon.png -define icon:auto-resize=256,128,64,48,32,16 assets/icon.ico

# 为 macOS 创建 ICNS 文件 (仅在 macOS 上执行)
if [[ "$OSTYPE" == "darwin"* ]]; then
    iconutil -c icns assets/icon.iconset -o assets/icon.icns
else
    echo "注意: 在非 macOS 系统上跳过 ICNS 文件生成"
    # 使用 ImageMagick 创建基本的 icns 文件
    magick convert assets/icon.png assets/icon.icns
fi

# 清理临时文件
rm -f assets/icon.svg
rm -rf assets/icon.iconset

echo "图标生成完成!"
echo "- Windows 图标: assets/icon.ico"
echo "- macOS 图标: assets/icon.icns"
echo "- 通用图标: assets/icon.png" 