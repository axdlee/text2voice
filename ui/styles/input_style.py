from .colors import Colors

class InputStyle:
    """输入框样式定义"""
    NORMAL = f"""
        QLineEdit, QTextEdit {{
            background-color: {Colors.SURFACE};
            border: 1px solid {Colors.BORDER};
            border-radius: 4px;
            padding: 8px;
            color: {Colors.TEXT};
            selection-background-color: {Colors.PRIMARY};
        }}
        QLineEdit:hover, QTextEdit:hover {{
            border-color: {Colors.HOVER};
        }}
        QLineEdit:focus, QTextEdit:focus {{
            border-color: {Colors.PRIMARY};
        }}
        QTextEdit {{
            font-size: 13px;
        }}
    """ 