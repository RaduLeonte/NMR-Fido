'''Initialize main window.'''

import sys

from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QApplication, QMainWindow, QGridLayout, QWidget


def start_app(args: list):
    app: QApplication = QApplication(args)

    window: MainWindow = MainWindow()
    window.show()

    app.exec()


class MainWindow(QMainWindow):
    '''
    Main window class.
    '''
    def __init__(self) -> None:
        super().__init__()
        
        # Window config
        self.setWindowTitle("NMR Fido")
        #self.setWindowIcon(QIcon("icon.png"))
        
        # Minimum size
        min_size = (700, 400)
        self.setMinimumSize(QSize(*min_size))
        
        # Set init size based on screen aspect ratio
        screen_size = QApplication.primaryScreen().availableSize()
        if screen_size.width() >= screen_size.height():
            app_width = int(screen_size.width()*(2/3))
            app_size = QSize(app_width, int(app_width*(min_size[1]/min_size[0])))
        else:
            app_height = int(screen_size.height()*(2/3))
            app_size = QSize(int(app_height*(min_size[0]/min_size[1])), app_height)
        self.resize(app_size)
        
        # Content
        content = QWidget(self)
        layout = QGridLayout(content)
        self.setCentralWidget(content)