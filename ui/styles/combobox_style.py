from .colors import Colors

class ComboBoxStyle:
    """下拉框样式定义"""
    NORMAL = f"""
        QComboBox {{
            background-color: {Colors.SURFACE};
            border: 1px solid {Colors.BORDER};
            border-radius: 4px;
            padding: 5px 10px;
            color: {Colors.TEXT};
            min-width: 150px;
            height: 30px;
        }}
        QComboBox:hover {{
            border-color: {Colors.HOVER};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        QComboBox::down-arrow {{
            image: url(resources/icons/down_arrow.png);
            width: 12px;
            height: 12px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {Colors.SURFACE};
            border: 1px solid {Colors.BORDER};
            selection-background-color: {Colors.HOVER};
            selection-color: {Colors.TEXT};
            outline: none;
        }}
    """ 