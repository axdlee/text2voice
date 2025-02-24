from .colors import Colors

class BaseStyle:
    """基础样式定义"""
    GLOBAL = f"""
        QWidget {{
            background-color: {Colors.BACKGROUND};
            color: {Colors.TEXT};
            font-family: -apple-system, "Microsoft YaHei", "PingFang SC", sans-serif;
        }}
        
        QLabel {{
            color: {Colors.TEXT_SECONDARY};
            font-size: 13px;
            background: transparent;
        }}
        
        QScrollBar:vertical {{
            border: none;
            background: {Colors.BACKGROUND};
            width: 8px;
            margin: 0px;
        }}
        QScrollBar::handle:vertical {{
            background: {Colors.SECONDARY};
            border-radius: 4px;
            min-height: 20px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {Colors.HOVER};
        }}
    """ 