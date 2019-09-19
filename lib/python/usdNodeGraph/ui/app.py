
import os
from usdNodeGraph.module.sqt import QApplication, QPalette, QColor, Qt
from usdNodeGraph.utils.res import resource


TEXT_COLOR = QColor(220, 220, 220)
DISABLED_COLOR = QColor(150, 150, 150)


class DarkPalette(QPalette):
    def __init__(self):
        super(DarkPalette, self).__init__()

        self.setColor(QPalette.Window, QColor(50, 50, 50))
        self.setColor(QPalette.WindowText, TEXT_COLOR)
        self.setColor(QPalette.Disabled, QPalette.WindowText, DISABLED_COLOR)

        self.setColor(QPalette.Text, TEXT_COLOR)
        self.setColor(QPalette.Disabled, QPalette.Text, DISABLED_COLOR)

        self.setColor(QPalette.ToolTipBase, TEXT_COLOR)
        self.setColor(QPalette.ToolTipText, QColor(50, 50, 50))

        self.setColor(QPalette.Base, QColor(40, 40, 40))
        self.setColor(QPalette.AlternateBase, QColor(60, 60, 60))

        self.setColor(QPalette.Dark, QColor(30, 30, 30))
        self.setColor(QPalette.Shadow, QColor(20, 20, 20))

        self.setColor(QPalette.Button, QColor(50, 50, 50))
        self.setColor(QPalette.ButtonText, TEXT_COLOR)
        self.setColor(QPalette.Disabled, QPalette.ButtonText, DISABLED_COLOR)

        self.setColor(QPalette.BrightText, QColor(200, 20, 20))
        self.setColor(QPalette.Link, QColor(40, 120, 200))

        self.setColor(QPalette.Highlight, QColor(40, 130, 200))
        self.setColor(QPalette.Disabled, QPalette.Highlight, QColor(120, 120, 120))

        self.setColor(QPalette.HighlightedText, QColor(40, 200, 200))
        self.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(120, 120, 120))


class MainApplication(QApplication):
    def __init__(self, *args, **kwargs):
        super(MainApplication, self).__init__(*args, **kwargs)

        darkPalette = DarkPalette()
        self.setPalette(darkPalette)

        guiStyle = resource.get_style('style')
        self.setStyleSheet(guiStyle)



