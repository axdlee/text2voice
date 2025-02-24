from .colors import Colors

class TableStyle:
    """表格样式定义"""
    NORMAL = f"""
        QTableWidget {{
            background-color: {Colors.SURFACE};
            border: none;
            gridline-color: {Colors.BORDER};
            outline: none;
        }}
        QTableWidget::item {{
            padding: 8px;
            color: {Colors.TEXT};
        }}
        QTableWidget::item:selected {{
            background-color: {Colors.HOVER};
        }}
        QHeaderView::section {{
            background-color: {Colors.BACKGROUND};
            color: {Colors.TEXT_SECONDARY};
            padding: 8px;
            border: none;
            border-bottom: 1px solid {Colors.BORDER};
        }}
    """ 