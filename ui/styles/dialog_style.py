from .colors import Colors

class DialogStyle:
    """对话框样式定义"""
    NORMAL = f"""
        QDialog {{
            background-color: {Colors.BACKGROUND};
            border: 1px solid {Colors.BORDER};
        }}
        QDialog QLabel {{
            color: {Colors.TEXT};
        }}
        QDialog QPushButton {{
            min-width: 80px;
        }}
        QMessageBox {{
            background-color: {Colors.BACKGROUND};
        }}
        QMessageBox QLabel {{
            color: {Colors.TEXT};
        }}
    """ 