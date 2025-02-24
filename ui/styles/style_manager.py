from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from .colors import Colors
from .base_style import BaseStyle
from .button_style import ButtonStyle
from .input_style import InputStyle
from .table_style import TableStyle
from .combobox_style import ComboBoxStyle
from .dialog_style import DialogStyle

class StyleManager:
    """样式管理器"""
    
    @classmethod
    def apply_style(cls, app: QApplication):
        """应用样式到应用程序"""
        # 组合所有样式
        style = "\n".join([
            BaseStyle.GLOBAL,
            ButtonStyle.NORMAL,
            ButtonStyle.SECONDARY,
            InputStyle.NORMAL,
            TableStyle.NORMAL,
            ComboBoxStyle.NORMAL,
            DialogStyle.NORMAL
        ])
        
        # 设置应用程序样式表
        app.setStyleSheet(style)
        
        # 设置调色板
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(Colors.BACKGROUND))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(Colors.TEXT))
        palette.setColor(QPalette.ColorRole.Base, QColor(Colors.SURFACE))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(Colors.HOVER))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(Colors.SURFACE))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(Colors.TEXT))
        palette.setColor(QPalette.ColorRole.Text, QColor(Colors.TEXT))
        palette.setColor(QPalette.ColorRole.Button, QColor(Colors.PRIMARY))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(Colors.TEXT))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(Colors.PRIMARY))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(Colors.TEXT))
        app.setPalette(palette) 