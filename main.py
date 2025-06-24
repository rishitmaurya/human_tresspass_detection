import sys
from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from gui.app import MainApp
import time
import os

def main():
    app = QApplication(sys.argv)

    # Show splash screen
    splash_pix = QPixmap(os.path.abspath("assets/zoneeye.png"))  
    splash_pix = splash_pix.scaled(600, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation) 
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.setMask(splash_pix.mask())
    splash.show()
    app.processEvents()

    # Simulate loading (or do actual initialization here)
    time.sleep(2)  

    window = MainApp()
    window.show()
    splash.finish(window)  

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()