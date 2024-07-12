import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QStackedWidget, QMessageBox
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt, QRect

user_cancelled = True  # Global flag to check if the user canceled

class PositionedImageWidget(QWidget):
    def __init__(self, image_path, parent=None, x=0, y=0, width=0, height=0):
        super().__init__(parent)
        self.image_path = image_path

        self.setGeometry(QRect(x, y, width, height))
        self.label = QLabel(self)
        self.label.setGeometry(self.rect())
        self.update_pixmap()
        self.setStyleSheet("background: transparent;")
        self.label.setStyleSheet("background: transparent;")

    def update_pixmap(self):
        pixmap = QPixmap(self.image_path)
        self.label.setPixmap(pixmap.scaled(self.label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def resizeEvent(self, event):
        self.label.setGeometry(self.rect())
        self.update_pixmap()
        super().resizeEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Sundial")
        self.setFixedSize(900, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        central_widget.setLayout(layout)

        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)

        self.page1 = QWidget()
        self.stacked_widget.addWidget(self.page1)
        self.setup_page1(self.page1)

        self.page2 = QWidget()
        self.stacked_widget.addWidget(self.page2)
        self.setup_page2(self.page2)

        self.page3 = QWidget()
        self.stacked_widget.addWidget(self.page3)
        self.setup_page3(self.page3)

    def get_static_path(self, filename):
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, 'sd_qt', 'static', filename)

    def setup_page1(self, page):
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        svg_path = self.get_static_path('Background_Image.svg')
        svg_widget = QSvgWidget(svg_path)
        layout.addWidget(svg_widget)

        positioned_image_path = self.get_static_path('Group_30513.png')
        logo_image_path = self.get_static_path('Sundial.svg')

        positioned_image_widget = PositionedImageWidget(positioned_image_path, page, 498, 66, 440, 568)
        positioned_image_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        positioned_image_widget.show()

        logo_widget = PositionedImageWidget(logo_image_path, page, 20, 20, 150, 36)
        logo_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        logo_widget.show()

        text_label = QLabel("Our Pledge to Privacy", page)
        text_label.setGeometry(50, 211, 380, 39)
        text_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        font = QFont("Poppins", 24, QFont.Weight.Normal)
        text_label.setFont(font)
        text_label.setStyleSheet("text-align: left;color: #474B4F; background: transparent; font: normal normal 600 28px/42px Poppins;opacity: 1;")
        text_label.setWordWrap(False)
        text_label.show()

        lorem_label1 = QLabel("Lorem Ipsum is simply dummy text of the printing industry. Lorem Ipsum has been the industry's standard text ever since the 1500s, when an unknown.", page)
        lorem_label1.setGeometry(50, 280, 332, 61)
        lorem_label1.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        font = QFont("Poppins", 12, QFont.Weight.Normal)
        lorem_label1.setFont(font)
        lorem_label1.setStyleSheet("text-align: left;color: #474B4F; background: transparent; font:normal normal normal 12px/22px Poppins;opacity: 1;")
        lorem_label1.setWordWrap(True)
        lorem_label1.show()

        lorem_label2 = QLabel("Lorem Ipsum is simply dummy text of the printing industry. Lorem Ipsum has been the industry's standard text ever since the 1500s, when an unknown.", page)
        lorem_label2.setGeometry(50, 361, 332, 61)
        lorem_label2.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        lorem_label2.setFont(QFont("Poppins", 12, QFont.Weight.Normal))
        lorem_label2.setStyleSheet("text-align: left;color: #474B4F; background: transparent;font: normal normal normal 12px/22px Arial;opacity: 1;")
        lorem_label2.setWordWrap(True)
        lorem_label2.show()

        back_button = QPushButton("Back", page)
        back_button.setGeometry(50, 452, 80, 40)
        back_button.setStyleSheet("background: #A1A3A5; border-radius: 5px; color: white;")
        back_button.clicked.connect(self.go_to_previous_page)
        back_button.show()

        new_button = QPushButton("Next", page)
        new_button.setGeometry(150, 452, 80, 40)
        new_button.setStyleSheet("""
            background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #1D0B77, stop:1 #6A5FA2);
            border-radius: 5px;
            color: white;
        """)
        new_button.clicked.connect(self.go_to_next_page)
        new_button.show()

    def setup_page2(self, page):
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        svg_path = self.get_static_path('Background_Image.svg')
        svg_widget = QSvgWidget(svg_path)
        layout.addWidget(svg_widget)

        positioned_image_path = self.get_static_path('Group_30513.png')
        logo_image_path = self.get_static_path('Sundial.svg')

        positioned_image_widget = PositionedImageWidget(positioned_image_path, page, 498, 66, 440, 568)
        positioned_image_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        positioned_image_widget.show()

        logo_widget = PositionedImageWidget(logo_image_path, page, 20, 20, 150, 36)
        logo_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        logo_widget.show()

        text_label = QLabel("Data Security & Encryption", page)
        text_label.setGeometry(50, 211, 380, 39)
        text_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        font = QFont("Poppins", 24, QFont.Weight.Normal)
        text_label.setFont(font)
        text_label.setStyleSheet("text-align: left;color: #474B4F; background: transparent; font: normal normal 600 28px/42px Poppins;opacity: 1;")
        text_label.setWordWrap(False)
        text_label.show()

        lorem_label1 = QLabel("Lorem Ipsum is simply dummy text of the printing industry. Lorem Ipsum has been the industry's standard text ever since the 1500s, when an unknown.", page)
        lorem_label1.setGeometry(50, 280, 332, 61)
        lorem_label1.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        font = QFont("Poppins", 12, QFont.Weight.Normal)
        lorem_label1.setFont(font)
        lorem_label1.setStyleSheet("text-align: left;color: #474B4F; background: transparent; font:normal normal normal 12px/22px Poppins;opacity: 1;")
        lorem_label1.setWordWrap(True)
        lorem_label1.show()

        lorem_label2 = QLabel("Lorem Ipsum is simply dummy text of the printing industry. Lorem Ipsum has been the industry's standard text ever since the 1500s, when an unknown.", page)
        lorem_label2.setGeometry(50, 361, 332, 61)
        lorem_label2.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        lorem_label2.setFont(QFont("Poppins", 12, QFont.Weight.Normal))
        lorem_label2.setStyleSheet("text-align: left;color: #474B4F; background: transparent;font: normal normal normal 12px/22px Arial;opacity: 1;")
        lorem_label2.setWordWrap(True)
        lorem_label2.show()

        back_button = QPushButton("Back", page)
        back_button.setGeometry(50, 452, 80, 40)
        back_button.setStyleSheet("background: #A1A3A5; border-radius: 5px; color: white;")
        back_button.clicked.connect(self.go_to_previous_page)
        back_button.show()

        new_button = QPushButton("Next", page)
        new_button.setGeometry(150, 452, 80, 40)
        new_button.setStyleSheet("""
            background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #1D0B77, stop:1 #6A5FA2);
            border-radius: 5px;
            color: white;
        """)
        new_button.clicked.connect(self.go_to_next_page)
        new_button.show()

    def setup_page3(self, page):
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove the margins

        # Load SVG background image
        svg_path = self.get_static_path('Background_Image.svg')
        svg_widget = QSvgWidget(svg_path)
        layout.addWidget(svg_widget)

        # Create and add the Sundial.svg image widget
        sundial_path = self.get_static_path('Sundial.svg')
        if not os.path.exists(sundial_path):
            print(f"Error: {sundial_path} does not exist.")
        else:
            logo_widget = PositionedImageWidget(sundial_path, page, 20, 20, 150, 36)
            logo_widget.setStyleSheet("background: transparent;")
            logo_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            logo_widget.show()
            print("Sundial.svg added successfully.")

        # Create and add the positioned image widget (Group_30501.svg)
        group_30501_path = self.get_static_path('Group_30501.png')
        if not os.path.exists(group_30501_path):
            print(f"Error: {group_30501_path} does not exist.")
        else:
            positioned_image_widget = PositionedImageWidget(group_30501_path, page, 522, 197, 293, 307)
            positioned_image_widget.setStyleSheet("background: transparent; opacity: 1;")
            positioned_image_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            positioned_image_widget.show()
            print("Group_30501.svg added successfully.")

        # Add the first text label with specified properties
        text_label = QLabel("Browser Compatibility", page)
        text_label.setGeometry(50, 211, 380, 39)
        text_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)  # Align left and vertically centered
        font = QFont("Poppins", 24, QFont.Weight.Bold)  # Adjust the font size if needed
        text_label.setFont(font)
        text_label.setStyleSheet("color: #474B4F; background: transparent; font: normal normal 600 28px/42px Poppins;opacity: 1;")
        text_label.setWordWrap(False)  # Disable word wrap

        # Add the second text label with specified properties
        lorem_label1 = QLabel("Lorem Ipsum is simply dummy text of the printing industry.", page)
        lorem_label1.setGeometry(50, 265, 332, 61)
        lorem_label1.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)  # Align left and top
        lorem_label1.setFont(QFont("Poppins", 12, QFont.Weight.Normal))  # Font with specified properties
        lorem_label1.setStyleSheet("""
            background: transparent;
            letter-spacing: 0px;
            color: #474B4F;
            opacity: 1;
            font: normal normal normal 12px/28px Poppins;
        """)
        lorem_label1.setWordWrap(True)  # Enable word wrap

        # Add the ellipses and text labels for browsers
        browsers = ["Firefox", "Google Chrome", "Opera", "Safari", "Vivaldi", "Microsoft Edge", "Brave", "Tor", "Pale Moon", "Waterfox"]
        x_pos = 50
        y_pos = 309

        for i, browser in enumerate(browsers):
            # Add the ellipse (circle) with specified properties
            ellipse = QWidget(page)
            ellipse.setGeometry(x_pos, y_pos, 6, 6)
            ellipse.setStyleSheet("""
                background-color: #A1A3A5;
                border-radius: 3px;
                opacity: 0.5;
            """)
            ellipse.show()

            browser_label = QLabel(browser, page)
            browser_label.setGeometry(x_pos + 16, y_pos - 6, 120, 19)  
            browser_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)  
            browser_label.setFont(QFont("Poppins", 12, QFont.Weight.Normal)) 
            browser_label.setStyleSheet("""
                background: transparent;
                letter-spacing: 0px;
                color: #474B4F;
                opacity: 1;
                font: normal normal normal 12px/28px Poppins;
            """)
            browser_label.show()

            y_pos += 29

            if i == 4:
                x_pos = 225
                y_pos = 309

        back_button = QPushButton("Back", page)
        back_button.setGeometry(50, 452, 80, 40)
        back_button.setStyleSheet("background: #A1A3A5; border-radius: 5px; color: white;")
        back_button.clicked.connect(self.go_to_previous_page)
        back_button.show()

        finish_button = QPushButton("Finish", page)
        finish_button.setGeometry(150, 452, 80, 40)
        finish_button.setStyleSheet("""
            background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #1D0B77, stop:1 #6A5FA2);
            border-radius: 5px;
            color: white;
        """)
        finish_button.clicked.connect(self.finish_process)
        finish_button.show()

    def go_to_next_page(self):
        current_index = self.stacked_widget.currentIndex()
        self.stacked_widget.setCurrentIndex(current_index + 1)

    def go_to_previous_page(self):
        current_index = self.stacked_widget.currentIndex()
        self.stacked_widget.setCurrentIndex(current_index - 1)

    def finish_process(self):
        global user_cancelled
        user_cancelled = False  # Set to False when the user finishes the process
        self.close()

    def closeEvent(self, event):
        if user_cancelled:
            event.accept()  # Automatically accept the event if user cancelled
        else:
            event.accept()

def main_method():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()

    # Check the user_cancelled flag to determine if the user canceled the process
    if user_cancelled:
        print("User canceled the process.")
        return 0
    else:
        print("User finished the process.")
        return 1

