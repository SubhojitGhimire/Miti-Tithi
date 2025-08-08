import sys
from PySide6.QtCore import Qt
from src.ui.main_window import MainWindow
from PySide6.QtWidgets import QApplication

def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    
    app.setApplicationName("NepaliCalendarDesktopWidget")
    app.setOrganizationName("SubhojitGhimire")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
