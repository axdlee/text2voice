from .colors import Colors

class ButtonStyle:
    """按钮样式定义"""
    NORMAL = f"""
        QPushButton {{
            background-color: {Colors.PRIMARY};
            color: {Colors.TEXT};
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-size: 13px;
            outline: none;
        }}
        QPushButton:hover {{
            background-color: {Colors.PRIMARY_LIGHT};
        }}
        QPushButton:pressed {{
            background-color: {Colors.PRIMARY_DARK};
        }}
    """
    
    SECONDARY = f"""
        QPushButton {{
            background-color: {Colors.SECONDARY};
            color: {Colors.TEXT};
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-size: 13px;
        }}
        QPushButton:hover {{
            background-color: {Colors.HOVER};
        }}
        QPushButton:pressed {{
            background-color: {Colors.PRESSED};
        }}
    """ 