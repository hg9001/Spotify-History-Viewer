import sys
from PyQt5.QtWidgets import QApplication
from streaming_viewer import StreamingHistoryViewer

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StreamingHistoryViewer()
    window.show()
    sys.exit(app.exec_())
