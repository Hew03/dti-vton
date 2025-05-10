import sys
from PyQt5.QtWidgets import QApplication
from ui import ClothingTryOnApp

def main():
    app = QApplication(sys.argv)
    window = ClothingTryOnApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
