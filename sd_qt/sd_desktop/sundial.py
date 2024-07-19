import json
import os
from pathlib import Path
import sys
import threading
import time
import webbrowser
from datetime import datetime, timedelta
import string
import random
import pytz
import requests
from PyQt6 import QtCore, QtGui, QtWidgets, QtQuickWidgets
from PyQt6.QtCore import Qt, QEvent, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QIcon, QAction, QCursor
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QGraphicsDropShadowEffect, QSystemTrayIcon, \
    QMenu
from pytz import tzinfo
from sd_core.cache import cache_user_credentials, delete_password, clear_all_credentials, get_credentials, \
    store_credentials, add_password
from sd_core.launch_start import launch_app, set_autostart_registry, delete_launch_app
from sd_qt.sd_desktop.toggleSwitch import QToggle


# Globals
events = []
list_view_events = []
colors = ["#FCEEFB", "#FFF5E8", "#EFECFF", "#D8E7F2", "#EBF2FC", "#E4E4E4", "#ECF6E4"]
current_color_index = 0
settings = {}
userdetails = {}
first_name = ""
week_schedule = {
    'Monday': True, 'Tuesday': True, 'Wednesday': True, 'Thursday': True,
    'Friday': True, 'Saturday': True, 'Sunday': True,
    'starttime': '9:30 AM', 'endtime': '6:30 PM'
}
default_week_schedule = week_schedule.copy()
current_directory = os.path.dirname(__file__)
folder_name = "resources"
folder_path = os.path.join(current_directory, folder_name)
TrayIconLogo = os.path.join(os.path.dirname(current_directory), "media")
sundial_widget = None
signin_ui = None
tray_icon = None
URI = None
host = "http://localhost:7600/api"

class TrayIcon(QSystemTrayIcon):
    def __init__(self, icon: QIcon, parent: QWidget = None):
        QSystemTrayIcon.__init__(self, icon, parent)
        print(icon)
        super().__init__(parent)
        self._parent = parent
        self.setIcon(icon)
        self.setToolTip("Sundial")
        self.activated.connect(self.on_tray_icon_activated)
        self._build_rootmenu()
        self.setContextMenu(self.menu)

    def _build_rootmenu(self):
        self.menu = QMenu(self._parent)
        
        if getattr(self, 'testing', False):
            self.menu.addAction("Running in testing mode")
            self.menu.addSeparator()
        
        self.menu.addAction("Open Sundial", self.bring_to_front)
        self.menu.addSeparator()
        exit_action = self.menu.addAction("Quit Sundial")
        exit_action.triggered.connect(self.quit)

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.setContextMenu(self.menu)
            self.contextMenu().exec(QCursor.pos())

    def bring_to_front(self):
        # Bring the main window to front and activate it
        if self._parent and isinstance(self._parent, QWidget):
            if not self._parent.isVisible():
                self._parent.show()
            if not self._parent.isActiveWindow():
                self._parent.setWindowState(self._parent.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
                self._parent.activateWindow()
                self._parent.raise_()
                self._parent.setFocus()

    def update_parent(self, new_parent):
        # Update the parent widget of the tray icon
        self._parent = new_parent

    def quit(self):
        # Clean up and quit the application
        from sd_core.util import stop_server
        stop_server()
        QApplication.instance().quit()


class Sundial(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(Sundial, self).__init__()
        self.displayed_events = set()
        self.setupUi(self)
        self.installEventFilter(self)
        self.credentials_timer = QTimer()
        self.signin_widget = None
        self.signin_ui = None
        self.sundial_widget = None

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.WindowActivate:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
            self.show()
        elif event.type() == QEvent.Type.WindowDeactivate:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
            self.show()
        return super().eventFilter(obj, event)

    def bring_to_front(self):
        self.raise_()
        self.activateWindow()
        self.setFocus()

    def showEvent(self, event):
        self.raise_()
        self.activateWindow()
        super(Sundial, self).showEvent(event)

    def setupUi(self, Widget):
        Widget.resize(1134, 712)
        Widget.setMinimumSize(QtCore.QSize(1134, 712))
        Widget.setMaximumSize(QtCore.QSize(1134, 712))
        Widget.setStyleSheet("background-color: rgb(255, 255, 255);")
        get_user_details()

        # Remove existing layout if any
        if Widget.layout() is not None:
            old_layout = Widget.layout()
            while old_layout.count():
                item = old_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
            QtWidgets.QWidget().setLayout(old_layout)

        self.horizontalLayout = QtWidgets.QHBoxLayout(Widget)
        self.horizontalLayout.setContentsMargins(-1, -1, -1, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")

        self.setupSidebar(Widget)
        self.horizontalLayout.addWidget(self.sidebar)

        self.setupStack(Widget)
        self.horizontalLayout.addWidget(self.stackedWidget)

        self.setupUserDrawer(Widget)
        self.connectSignals()

    def setupSidebar(self, Widget):
        self.sidebar = QtWidgets.QWidget(parent=Widget)
        self.sidebar.setEnabled(True)
        self.sidebar.setMinimumSize(QtCore.QSize(200, 670))
        self.sidebar.setMaximumSize(QtCore.QSize(200, 700))
        self.sidebar.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.sidebar.setObjectName("sidebar")

        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.sidebar)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")

        self.SundialLogo = QtWidgets.QWidget(parent=self.sidebar)
        self.SundialLogo.setMinimumSize(QtCore.QSize(0, 40))
        self.SundialLogo.setMaximumSize(QtCore.QSize(16777215, 40))
        self.SundialLogo.setObjectName("SundialLogo")
        self.label = QtWidgets.QLabel(parent=self.SundialLogo)
        self.label.setGeometry(QtCore.QRect(30, 0, 113, 40))
        self.label.setText("")
        self.label.setPixmap(QtGui.QPixmap(folder_path + "/Logo.svg"))
        self.label.setObjectName("label")
        self.verticalLayout_2.addWidget(self.SundialLogo)

        self.setupSidebarButtons()
        self.widget = QtWidgets.QWidget(parent=self.sidebar)
        self.widget.setMinimumSize(QtCore.QSize(0, 30))
        self.widget.setMaximumSize(QtCore.QSize(16777215, 100))
        self.widget.setObjectName("widget")

        self.pushButton = QtWidgets.QPushButton(parent=self.widget)
        self.pushButton.setGeometry(QtCore.QRect(183, 536, 534, 64))
        self.pushButton.setStyleSheet("border:none;\n")
        self.username_widget = QPushButton(parent=self.widget)
        self.username_widget.setGeometry(QtCore.QRect(10, 0, 181, 41))
        self.username_widget.setMinimumSize(QtCore.QSize(0, 0))
        self.username_widget.setObjectName("username_widget")
        self.username_widget.setStyleSheet("""
                    QPushButton:hover {
                        border: none; 
                        background: qlineargradient(
                            x1: 0, y1: 0, x2: 1, y2: 0,
                            stop: 0 rgba(232, 230, 241, 1),
                            stop: 1 rgba(232, 230, 241, 0.1)
                        );
                    }
                    QPushButton {
                        border: none;
                    }
                    QLabel {
                        background: transparent;
                    }
                """)
        self.username_icon = QtWidgets.QLabel(parent=self.username_widget)
        self.username_icon.setGeometry(QtCore.QRect(7, 10, 151, 21))
        self.username_icon.setText("")
        self.username_icon.setPixmap(QtGui.QPixmap(folder_path + "/defaultuser.svg"))
        self.username_icon.setObjectName("username_icon")
        self.username_label = QtWidgets.QLabel(parent=self.username_widget)
        self.username_label.setGeometry(QtCore.QRect(35, 13, 130, 16))

        font = QtGui.QFont()
        font.setPointSize(14)
        self.username_label.setFont(font)
        self.username_label.setObjectName("username_label")

        self.Signout = QPushButton(parent=self.widget)
        self.Signout.setGeometry(QtCore.QRect(10, 50, 181, 41))
        self.Signout.setMinimumSize(QtCore.QSize(0, 0))
        self.Signout.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.Signout.setObjectName("Signout")
        self.Signout.setStyleSheet("""
            QPushButton{
             border:none; 
            }  
            QPushButton:hover { 
                background-color: #FFEDED !important;
                border:none; 
            }
            QLabel {
                background: transparent;
            }
        """)

        self.Signout_logo = QtWidgets.QLabel(parent=self.Signout)
        self.Signout_logo.setGeometry(QtCore.QRect(7, 10, 21, 21))
        self.Signout_logo.setText("")
        self.Signout_logo.setPixmap(QtGui.QPixmap(folder_path + "/signout.svg"))
        self.Signout_logo.setObjectName("Signout_logo")

        self.SignOut_label = QtWidgets.QLabel(parent=self.Signout)
        self.SignOut_label.setGeometry(QtCore.QRect(35, 13, 111, 16))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.SignOut_label.setFont(font)
        self.SignOut_label.setObjectName("SignOut_label")
        self.SignOut_label.setText("Sign Out")

        self.verticalLayout_2.addWidget(self.widget)

    def setupSidebarButtons(self):
        self.widget_6 = QtWidgets.QWidget(parent=self.sidebar)
        self.widget_6.setMinimumSize(QtCore.QSize(0, 420))
        self.widget_6.setObjectName("widget_6")

        self.Activity = QPushButton(parent=self.widget_6)
        self.Activity.setGeometry(QtCore.QRect(10, 10, 181, 41))
        self.Activity.setMinimumSize(QtCore.QSize(0, 0))
        self.Activity.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.Activity.setStyleSheet("""
            QPushButton:hover {
                border: none; 
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 rgba(232, 230, 241, 1),
                    stop: 1 rgba(232, 230, 241, 0.1)
                );
            }
            QPushButton {
                border: none;
            }
            QLabel {
                background: transparent;
            }
        """)
        self.Activity.setObjectName("Activity")
        self.Activity_icon = QtWidgets.QLabel(parent=self.Activity)
        self.Activity_icon.setGeometry(QtCore.QRect(10, 10, 21, 21))
        self.Activity_icon.setText("")
        self.Activity_icon.setPixmap(QtGui.QPixmap(folder_path + "/Activity.svg"))
        self.Activity_icon.setObjectName("Activity_icon")

        self.Activity_label = QtWidgets.QLabel(parent=self.Activity)
        self.Activity_label.setGeometry(QtCore.QRect(35, 13, 111, 16))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.Activity_label.setFont(font)
        self.Activity_label.setObjectName("Activity_label")

        self.settings = QPushButton(parent=self.widget_6)
        self.settings.setGeometry(QtCore.QRect(10, 60, 181, 41))
        self.settings.setMinimumSize(QtCore.QSize(0, 0))
        self.settings.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.settings.setStyleSheet("""
            QPushButton:hover {
                border: none;  
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 rgba(232, 230, 241, 1),
                    stop: 1 rgba(232, 230, 241, 0.1)
                );
            }
            QPushButton {
                border: none;
            }
            QLabel {
                background: transparent;
            }
        """)
        self.settings.setObjectName("settings")
        self.settings_logo = QtWidgets.QLabel(parent=self.settings)
        self.settings_logo.setGeometry(QtCore.QRect(7, 10, 21, 21))
        self.settings_logo.setText("")
        self.settings_logo.setPixmap(QtGui.QPixmap(folder_path + "/generalSettings.svg"))
        self.settings_logo.setObjectName("settings_logo")
        self.settings_label = QtWidgets.QLabel(parent=self.settings)
        self.settings_label.setGeometry(QtCore.QRect(35, 13, 111, 16))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.settings_label.setFont(font)
        self.settings_label.setObjectName("settings_label")

        self.schedule = QPushButton(parent=self.widget_6)
        self.schedule.setGeometry(QtCore.QRect(10, 110, 181, 41))
        self.schedule.setMinimumSize(QtCore.QSize(0, 0))
        self.schedule.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.schedule.setStyleSheet("""
            QPushButton:hover {
                border: none;  
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 rgba(232, 230, 241, 1),
                    stop: 1 rgba(232, 230, 241, 0.1)
                );
            }
            QPushButton {
                border: none;
            }
            QLabel {
                background: transparent;
            }
        """)
        self.schedule.setObjectName("schedule")
        self.schedule_logo = QtWidgets.QLabel(parent=self.schedule)
        self.schedule_logo.setGeometry(QtCore.QRect(7, 10, 21, 21))
        self.schedule_logo.setText("")
        self.schedule_logo.setPixmap(QtGui.QPixmap(folder_path + "/schedule.svg"))
        self.schedule_logo.setObjectName("schedule_logo")
        self.schedule_label = QtWidgets.QLabel(parent=self.schedule)
        self.schedule_label.setGeometry(QtCore.QRect(35, 13, 111, 16))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.schedule_label.setFont(font)
        self.schedule_label.setObjectName("schedule_label")

        self.Version = QPushButton(parent=self.widget_6)
        self.Version.setGeometry(QtCore.QRect(10, 160, 181, 41))
        self.Version.setMinimumSize(QtCore.QSize(0, 0))
        self.Version.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.Version.setStyleSheet("""
            QPushButton:hover {
                border: none;  
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 rgba(232, 230, 241, 1),
                    stop: 1 rgba(232, 230, 241, 0.1)
                );
            }
            QPushButton {
                border: none;
            }
            QLabel {
                background: transparent;
            }
        """)
        self.Version.setObjectName("Version")
        self.Version_icon = QtWidgets.QLabel(parent=self.Version)
        self.Version_icon.setGeometry(QtCore.QRect(7, 10, 21, 21))
        self.Version_icon.setText("")
        self.Version_icon.setPixmap(QtGui.QPixmap(folder_path + "/version.svg"))
        self.Version_icon.setObjectName("Version_icon")
        self.Version_label = QtWidgets.QLabel(parent=self.Version)
        self.Version_label.setGeometry(QtCore.QRect(35, 13, 111, 16))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.Version_label.setFont(font)
        self.Version_label.setObjectName("Version_label")

        self.verticalLayout_2.addWidget(self.widget_6)

    def setupStack(self, Widget):
        self.stackedWidget = QtWidgets.QStackedWidget(parent=Widget)
        self.stackedWidget.setMinimumSize(QtCore.QSize(1134, 0))
        self.stackedWidget.setMaximumSize(QtCore.QSize(1134, 16777215))
        self.stackedWidget.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.stackedWidget.setObjectName("stackedWidget")

        self.setupActivitiesPage()
        self.setupGeneralSettingsPage()
        self.setupSchedulePage()
        self.setupVersionPage()

        self.stackedWidget.addWidget(self.Activites)
        self.stackedWidget.addWidget(self.GeneralSettings)
        self.stackedWidget.addWidget(self.Schedule)
        self.stackedWidget.addWidget(self.Version_and_update)

    def setupActivitiesPage(self):
        self.Activites = QtWidgets.QWidget()
        self.Activites.setObjectName("Activites")
        self.Activites_header = QtWidgets.QLabel(parent=self.Activites)
        self.Activites_header.setGeometry(QtCore.QRect(10, 0, 191, 31))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.Activites_header.setFont(font)
        self.Activites_header.setObjectName("Activites_header")

        self.Date_display = QtWidgets.QWidget(parent=self.Activites)
        self.Date_display.setGeometry(QtCore.QRect(10, 60, 851, 51))
        self.Date_display.setStyleSheet("background-color: #EFEFEF;\n"
                                        "border-top-left-radius: 10px;\n"
                                        "border-top-right-radius: 10px;\n"
                                        "border-bottom-right-radius: 0px;\n"
                                        "border-bottom-left-radius: 0px;\n"
                                        "")
        self.Date_display.setObjectName("Date_display")

        self.Day = QtWidgets.QLabel(parent=self.Date_display)
        self.Day.setGeometry(QtCore.QRect(22, 17, 58, 16))
        self.Day.setObjectName("Day")
        self.Day.setText("Day Text")

        self.Date = QtWidgets.QLabel(parent=self.Date_display)
        self.Date.setGeometry(QtCore.QRect(60, 18, 100, 16))
        self.Date.setObjectName("Date")
        self.Date.setText(f" -  {datetime.today().date()}")

        self.scrollArea = QtWidgets.QScrollArea(self.Activites)
        self.scrollArea.setGeometry(QtCore.QRect(10, 110, 851, 571))
        self.scrollArea.setStyleSheet("border:None;\nbackground-color:#F9F9F9;")
        self.scrollArea.verticalScrollBar().setStyleSheet("width: 0px;")
        self.scrollArea.horizontalScrollBar().setStyleSheet("height: 0px;")
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")

        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 851, 571))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")

        self.layout = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.layout.setContentsMargins(0, 0, 0, 10)
        self.layout.setSpacing(10)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.add_dynamic_blocks()

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.add_dynamic_blocks)
        self.timer.start(60000)

    def setupGeneralSettingsPage(self):
        self.GeneralSettings = QtWidgets.QWidget()
        self.GeneralSettings.setObjectName("GeneralSettings")

        self.GeneralSettings_header = QtWidgets.QLabel(parent=self.GeneralSettings)
        self.GeneralSettings_header.setGeometry(QtCore.QRect(0, 0, 191, 31))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.GeneralSettings_header.setFont(font)
        self.GeneralSettings_header.setObjectName("GeneralSettings_header")

        self.startup = QtWidgets.QWidget(parent=self.GeneralSettings)
        self.startup.setGeometry(QtCore.QRect(0, 56, 861, 80))
        self.startup.setStyleSheet("border-radius: 10px;\nbackground-color:#F9F9F9;")
        self.startup.setObjectName("startup")

        self.startup_label = QtWidgets.QLabel(parent=self.startup)
        self.startup_label.setGeometry(QtCore.QRect(20, 30, 211, 16))
        self.startup_label.setObjectName("startup_label")

        self.startup_checkbox = QToggle(parent=self.startup)
        self.startup_checkbox.setFixedHeight(20)
        self.startup_checkbox.setGeometry(QtCore.QRect(800, 30, 100, 21))
        self.startup_checkbox.setFont(QFont('Segoe Print', 10))
        self.startup_checkbox.setStyleSheet("QToggle{"
                                            "qproperty-bg_color:#A2A4A6;"
                                            "qproperty-circle_color:#FFFFFF;"
                                            "qproperty-active_color:#FA9C2B;"
                                            "qproperty-disabled_color:#777;"
                                            "qproperty-text_color:#A0F;}")
        self.startup_checkbox.setDuration(100)
        self.startup_checkbox.setChecked(True)
        self.startup_checkbox.stateChanged.connect(self.launchOnStart)

    def setupSchedulePage(self):
        self.Schedule = QtWidgets.QWidget()
        self.Schedule.setObjectName("Schedule")

        self.Schedule_label = QtWidgets.QLabel(parent=self.Schedule)
        self.Schedule_label.setGeometry(QtCore.QRect(20, 0, 131, 31))
        font = QtGui.QFont()
        font.setPointSize(24)
        self.Schedule_label.setFont(font)
        self.Schedule_label.setObjectName("Schedule_label")

        self.Schedule_enabler = QtWidgets.QWidget(parent=self.Schedule)
        self.Schedule_enabler.setGeometry(QtCore.QRect(20, 60, 861, 80))
        self.Schedule_enabler.setStyleSheet("border-radius: 10px;\nbackground-color:#F9F9F9;")
        self.Schedule_enabler.setObjectName("Schedule_enabler")

        self.Schedule_enabler_label = QtWidgets.QLabel(parent=self.Schedule_enabler)
        self.Schedule_enabler_label.setGeometry(QtCore.QRect(20, 30, 311, 16))
        self.Schedule_enabler_label.setObjectName("Schedule_enabler_label")

        self.Schedule_enabler_checkbox = QToggle(parent=self.Schedule_enabler)
        self.Schedule_enabler_checkbox.setGeometry(QtCore.QRect(800, 30, 100, 21))
        self.Schedule_enabler_checkbox.setStyleSheet("QToggle{"
                                                     "qproperty-bg_color:#A2A4A6;"
                                                     "qproperty-circle_color:#FFFFFF;"
                                                     "qproperty-active_color:#FA9C2B;"
                                                     "qproperty-disabled_color:#777;"
                                                     "qproperty-text_color:#A0F;}")
        self.Schedule_enabler_checkbox.setFixedHeight(20)
        self.Schedule_enabler_checkbox.setDuration(100)
        self.Schedule_enabler_checkbox.setChecked(settings['schedule'])

        self.widget_14 = QtWidgets.QWidget(parent=self.Schedule)
        self.widget_14.setGeometry(QtCore.QRect(20, 144, 861, 251))
        self.widget_14.setStyleSheet(" QWidget {\nborder-radius: 10px;\nbackground-color: #F9F9F9;\n}")
        self.widget_14.setObjectName("widget_14")

        self.Working_days_label = QtWidgets.QLabel(parent=self.widget_14)
        self.Working_days_label.setGeometry(QtCore.QRect(20, 10, 311, 16))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.Working_days_label.setFont(font)
        self.Working_days_label.setObjectName("Working_days_label")

        self.setupScheduleCheckboxes()
        self.Working_hours_label = QtWidgets.QLabel(parent=self.widget_14)
        self.Working_hours_label.setGeometry(QtCore.QRect(20, 90, 111, 16))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.Working_hours_label.setFont(font)
        self.Working_hours_label.setObjectName("Working_hours_label")

        self.From_time = QtWidgets.QTimeEdit(parent=self.widget_14)
        self.From_time.setGeometry(QtCore.QRect(20, 130, 211, 41))
        self.From_time.setStyleSheet("""
            QTimeEdit {
                border: 1px solid #DDDDDD;
                background-color: none;
                border-radius: 5px;
            }
            QTimeEdit::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 20px;
                border-width: 1px;
                border-color: #DDDDDD;
                border-style: solid;
                border-top-right-radius: 5px;
            }
            QTimeEdit::up-button:hover {
                background-color: #E6E6E6;
            }
            QTimeEdit::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 20px;
                border-width: 1px;
                border-color: #DDDDDD;
                border-style: solid;
                border-bottom-right-radius: 5px;
            }
            QTimeEdit::down-button:hover {
                background-color: #E6E6E6;
            }
        """)
        self.From_time.setObjectName("From_time")

        self.To_time = QtWidgets.QTimeEdit(parent=self.widget_14)
        self.To_time.setGeometry(QtCore.QRect(260, 130, 211, 41))
        self.To_time.setStyleSheet("""
            QTimeEdit {
                border: 1px solid #DDDDDD;
                background-color: none;
                border-radius: 5px;
            }
            QTimeEdit::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 20px;
                border-width: 1px;
                border-color: #DDDDDD;
                border-style: solid;
                border-top-right-radius: 5px;
            }
            QTimeEdit::up-button:hover {
                background-color: #E6E6E6;
            }
            QTimeEdit::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 20px;
                border-width: 1px;
                border-color: #DDDDDD;
                border-style: solid;
                border-bottom-right-radius: 5px;
            }
            QTimeEdit::down-button:hover {
                background-color: #E6E6E6;
            }
        """)
        self.To_time.setObjectName("To_time")

        self.From_time.timeChanged.connect(self.update_to_time_min)
        self.To_time.timeChanged.connect(self.update_from_time_max)
        self.updateCheckboxStates()

        self.result_label = QLabel(self.widget_14)
        self.result_label.setGeometry(QtCore.QRect(20, 180, 450, 30))

        self.To_time.timeChanged.connect(self.compare_times)
        self.From_time.timeChanged.connect(self.compare_times)

        self.Reset = QtWidgets.QPushButton(parent=self.widget_14)
        self.Reset.setGeometry(QtCore.QRect(600, 180, 111, 51))
        self.Reset.setStyleSheet("background-color: #FFFFFF  !important;\ncolor:#1D0B77;\n"
                                 "border: 1px solid #1D0B77;\nborder-radius: 5px;")
        self.Reset.setText("Save")
        self.Reset.clicked.connect(self.resetSchedule)

        self.Save = QtWidgets.QPushButton(parent=self.widget_14)
        self.Save.setGeometry(QtCore.QRect(720, 180, 111, 51))
        self.Save.setStyleSheet(
            "background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #1D0B77, stop:1 #6A5FA2);\n"
            "border-radius: 5px;\ncolor: #FFFFFF;\nborder: 1px solid #1D0B77;")
        self.Save.setText("Save")
        self.Save.clicked.connect(self.saveSchedule)

        self.widget_14.raise_()
        self.Schedule_label.raise_()
        self.Schedule_enabler.raise_()

        self.widget_14.setVisible(settings['schedule'])

        self.Schedule_enabler_checkbox.stateChanged.connect(self.toggle_schedule_visibility)

    def setupScheduleCheckboxes(self):
        self.monday_checkbox = QtWidgets.QCheckBox(parent=self.widget_14)
        self.monday_checkbox.setGeometry(QtCore.QRect(20, 50, 50, 40))
        self.monday_checkbox.setStyleSheet(".QCheckBox::indicator {\nwidth: 40px;\nheight: 40px;\n}")
        self.monday_checkbox.setText("")
        self.monday_checkbox.setIconSize(QtCore.QSize(40, 40))
        self.monday_checkbox.setObjectName("monday_checkbox")
        # self.monday_checkbox.setChecked(True)  # Checked by default
        self.monday_label = QtWidgets.QLabel(parent=self.widget_14)
        self.monday_label.setGeometry(QtCore.QRect(45, 50, 50, 40))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.monday_label.setFont(font)
        self.monday_label.setObjectName("monday_label")

        self.Tuesday_checkbox = QtWidgets.QCheckBox(parent=self.widget_14)
        self.Tuesday_checkbox.setGeometry(QtCore.QRect(120, 50, 40, 40))
        self.Tuesday_checkbox.setStyleSheet(".QCheckBox::indicator {\nwidth: 40px;\nheight: 40px;\n}")
        self.Tuesday_checkbox.setText("")
        self.Tuesday_checkbox.setIconSize(QtCore.QSize(40, 40))
        self.Tuesday_checkbox.setObjectName("Tuesday_checkbox")
        # self.Tuesday_checkbox.setChecked(True)  # Checked by default
        self.Tuesday_label = QtWidgets.QLabel(parent=self.widget_14)
        self.Tuesday_label.setGeometry(QtCore.QRect(145, 50, 60, 40))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.Tuesday_label.setFont(font)
        self.Tuesday_label.setObjectName("Tuesday_label")

        self.Wednesday_checkBox = QtWidgets.QCheckBox(parent=self.widget_14)
        self.Wednesday_checkBox.setGeometry(QtCore.QRect(220, 50, 40, 40))
        self.Wednesday_checkBox.setStyleSheet(".QCheckBox::indicator {\nwidth: 40px;\nheight: 40px;\n}")
        self.Wednesday_checkBox.setText("")
        self.Wednesday_checkBox.setIconSize(QtCore.QSize(40, 40))
        self.Wednesday_checkBox.setObjectName("Wednesday_checkBox")
        # self.Wednesday_checkBox.setChecked(True)  # Checked by default
        self.Wednesday_label = QtWidgets.QLabel(parent=self.widget_14)
        self.Wednesday_label.setGeometry(QtCore.QRect(245, 50, 100, 40))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.Wednesday_label.setFont(font)
        self.Wednesday_label.setObjectName("Wednesday_label")

        self.Thursday_checkbox = QtWidgets.QCheckBox(parent=self.widget_14)
        self.Thursday_checkbox.setGeometry(QtCore.QRect(330, 50, 40, 40))
        self.Thursday_checkbox.setStyleSheet(".QCheckBox::indicator {\nwidth: 40px;\nheight: 40px;\n}")
        self.Thursday_checkbox.setText("")
        self.Thursday_checkbox.setIconSize(QtCore.QSize(40, 40))
        self.Thursday_checkbox.setObjectName("Thursday_checkbox")
        # self.Thursday_checkbox.setChecked(True)  # Checked by default
        self.Thursday_label = QtWidgets.QLabel(parent=self.widget_14)
        self.Thursday_label.setGeometry(QtCore.QRect(355, 50, 100, 40))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.Thursday_label.setFont(font)
        self.Thursday_label.setObjectName("Thursday_label")

        self.Friday_checkBox = QtWidgets.QCheckBox(parent=self.widget_14)
        self.Friday_checkBox.setGeometry(QtCore.QRect(430, 50, 40, 40))
        self.Friday_checkBox.setStyleSheet(".QCheckBox::indicator {\nwidth: 40px;\nheight: 40px;\n}")
        self.Friday_checkBox.setText("")
        self.Friday_checkBox.setIconSize(QtCore.QSize(40, 40))
        self.Friday_checkBox.setObjectName("Friday_checkBox")
        # self.Friday_checkBox.setChecked(True)  # Checked by default
        self.Friday_label = QtWidgets.QLabel(parent=self.widget_14)
        self.Friday_label.setGeometry(QtCore.QRect(455, 50, 60, 40))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.Friday_label.setFont(font)
        self.Friday_label.setObjectName("Friday_label")

        self.saturday_checkBox = QtWidgets.QCheckBox(parent=self.widget_14)
        self.saturday_checkBox.setGeometry(QtCore.QRect(530, 50, 40, 40))
        self.saturday_checkBox.setStyleSheet(".QCheckBox::indicator {\nwidth: 40px;\nheight: 40px;\n}")
        self.saturday_checkBox.setText("")
        self.saturday_checkBox.setIconSize(QtCore.QSize(40, 40))
        self.saturday_checkBox.setObjectName("saturday_checkBox")
        # self.saturday_checkBox.setChecked(True)  # Checked by default
        self.Saturday_label = QtWidgets.QLabel(parent=self.widget_14)
        self.Saturday_label.setGeometry(QtCore.QRect(555, 50, 60, 40))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.Saturday_label.setFont(font)
        self.Saturday_label.setObjectName("Saturday_label")

        self.Sunday_checkBox = QtWidgets.QCheckBox(parent=self.widget_14)
        self.Sunday_checkBox.setGeometry(QtCore.QRect(630, 50, 40, 40))
        self.Sunday_checkBox.setStyleSheet(".QCheckBox::indicator {\nwidth: 40px;\nheight: 40px;\n}")
        self.Sunday_checkBox.setText("")
        self.Sunday_checkBox.setIconSize(QtCore.QSize(40, 40))
        self.Sunday_checkBox.setObjectName("Sunday_checkBox")
        # self.Sunday_checkBox.setChecked(True)  # Checked by default
        self.Sunday_label_2 = QtWidgets.QLabel(parent=self.widget_14)
        self.Sunday_label_2.setGeometry(QtCore.QRect(655, 50, 60, 40))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.Sunday_label_2.setFont(font)
        self.Sunday_label_2.setObjectName("Sunday_label_2")

        self.monday_checkbox.stateChanged.connect(self.update_week_schedule)
        self.Tuesday_checkbox.stateChanged.connect(self.update_week_schedule)
        self.Wednesday_checkBox.stateChanged.connect(self.update_week_schedule)
        self.Thursday_checkbox.stateChanged.connect(self.update_week_schedule)
        self.Friday_checkBox.stateChanged.connect(self.update_week_schedule)
        self.saturday_checkBox.stateChanged.connect(self.update_week_schedule)
        self.Sunday_checkBox.stateChanged.connect(self.update_week_schedule)

    def setupVersionPage(self):
        self.Version_and_update = QtWidgets.QWidget()
        self.Version_and_update.setObjectName("Version_and_update")

        self.Schedule_label_2 = QtWidgets.QLabel(parent=self.Version_and_update)
        self.Schedule_label_2.setGeometry(QtCore.QRect(10, 0, 191, 31))
        font = QtGui.QFont()
        font.setPointSize(24)
        self.Schedule_label_2.setFont(font)
        self.Schedule_label_2.setObjectName("Schedule_label_2")

        self.Version_2 = QtWidgets.QWidget(parent=self.Version_and_update)
        self.Version_2.setGeometry(QtCore.QRect(10, 60, 861, 61))
        self.Version_2.setStyleSheet("border-radius: 10px;\nbackground-color:#F9F9F9;")
        self.Version_2.setObjectName("Version_2")

        self.version_details = QtWidgets.QLabel(parent=self.Version_2)
        self.version_details.setGeometry(QtCore.QRect(20, 20, 311, 16))
        self.version_details.setObjectName("version_details")

    def setupUserDrawer(self, Widget):
        self.widget_2 = QtQuickWidgets.QQuickWidget(parent=Widget)
        self.widget_2.setGeometry(QtCore.QRect(240, 450, 391, 200))
        self.widget_2.setObjectName("widget_2")
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(10)
        shadow_effect.setOffset(2, 2)
        shadow_effect.setColor(QColor(0, 0, 0, 50))

        self.widget_2.setGraphicsEffect(shadow_effect)
        self.widget_2.setStyleSheet("border-radius: 10px;")

        font = QtGui.QFont()
        font.setPointSize(14)

        self.FirstName = QtWidgets.QLabel("First Name:", parent=self.widget_2)
        self.FirstName.setGeometry(QtCore.QRect(20, 40, 121, 16))
        self.FirstName.setObjectName("FirstName")
        self.FirstName.setFont(font)

        self.Lastname = QtWidgets.QLabel("Last Name:", parent=self.widget_2)
        self.Lastname.setGeometry(QtCore.QRect(20, 80, 121, 16))
        self.Lastname.setObjectName("Lastname")
        self.Lastname.setFont(font)

        self.Email = QtWidgets.QLabel("Email:", parent=self.widget_2)
        self.Email.setGeometry(QtCore.QRect(20, 120, 121, 16))
        self.Email.setObjectName("Email")
        self.Email.setFont(font)

        self.mobile = QtWidgets.QLabel("Mobile:", parent=self.widget_2)
        self.mobile.setGeometry(QtCore.QRect(20, 160, 121, 16))
        self.mobile.setObjectName("mobile")
        self.mobile.setFont(font)

        self.first_name_value = QtWidgets.QLabel(parent=self.widget_2)
        self.first_name_value.setGeometry(QtCore.QRect(150, 40, 221, 16))
        self.first_name_value.setObjectName("first_name_value")
        self.first_name_value.setFont(font)

        self.last_name_value = QtWidgets.QLabel(parent=self.widget_2)
        self.last_name_value.setGeometry(QtCore.QRect(150, 80, 221, 16))
        self.last_name_value.setObjectName("last_name_value")
        self.last_name_value.setFont(font)

        self.email_value = QtWidgets.QLabel(parent=self.widget_2)
        self.email_value.setGeometry(QtCore.QRect(150, 120, 221, 16))
        self.email_value.setObjectName("email_value")
        self.email_value.setFont(font)

        self.mobile_value = QtWidgets.QLabel(parent=self.widget_2)
        self.mobile_value.setGeometry(QtCore.QRect(150, 160, 221, 16))
        self.mobile_value.setObjectName("mobile_value")
        self.mobile_value.setFont(font)

        self.widget_2.hide()
        self.retranslateUi(Widget)

    def connectSignals(self):
        self.Activity.clicked.connect(lambda: self.change_page(0, self.Activity))
        self.settings.clicked.connect(lambda: self.change_page(1, self.settings))
        self.schedule.clicked.connect(lambda: self.change_page(2, self.schedule))
        self.Version.clicked.connect(lambda: self.change_page(3, self.Version))
        self.Signout.clicked.connect(self.sign_out)

        self.username_widget.clicked.connect(self.toggle_user_drawer)

        self.buttons = [self.Activity, self.settings, self.schedule, self.Version]

    def change_page(self, index, clicked_button):
        self.widget_2.hide()
        self.stackedWidget.setCurrentIndex(index)

    def update_to_time_min(self, time):
        self.To_time.setMinimumTime(time)

    def update_from_time_max(self, time):
        self.From_time.setMaximumTime(time)

    def toggle_schedule_visibility(self):
        if self.Schedule_enabler_checkbox.isChecked():
            self.widget_14.setVisible(True)
            QApplication.processEvents()
        else:
            self.widget_14.setVisible(False)
            QApplication.processEvents()
        QApplication.processEvents()
        threading.Thread(target=self.run_add_settings).start()

    def run_add_settings(self):
        add_settings('schedule', self.Schedule_enabler_checkbox.isChecked())

    def toggle_user_drawer(self):
        if self.widget_2.isVisible():
            self.widget_2.setVisible(False)
        else:
            user_details()
            self.widget_2.setVisible(True)
            self.first_name_value.setText(userdetails['firstname'])
            self.last_name_value.setText(userdetails['lastname'])
            self.email_value.setText(userdetails['email'])
            self.mobile_value.setText(userdetails['phone'])

    def retranslateUi(self, Widget):
        _translate = QtCore.QCoreApplication.translate
        Widget.setWindowTitle(_translate("Widget", "TTim"))
        self.Activity_label.setText(_translate("Widget", "Activities"))
        self.settings_label.setText(_translate("Widget", "General Settings"))
        self.schedule_label.setText(_translate("Widget", "Schedule"))
        self.Version_label.setText(_translate("Widget", "Version & Update"))
        self.SignOut_label.setText(_translate("Widget", "Sign out"))
        self.username_label.setText(_translate("Widget", f"Hello {first_name}"))
        self.username_label.setToolTip(f"Hello {first_name}")
        self.Activites_header.setText(_translate("Widget", "Activities"))
        self.GeneralSettings_header.setText(_translate("Widget", "General settings"))
        self.Day.setText(_translate("Widget", "Today"))
        self.startup_label.setText(_translate("Widget", "Launch sundial on system startup"))
        self.Schedule_label.setText(_translate("Widget", "Schedule"))
        self.Schedule_enabler_label.setText(_translate("Widget", "Record data only during my scheduled work hours."))
        self.Working_days_label.setText(_translate("Widget", "Working days"))
        self.monday_label.setText(_translate("Widget", "Monday"))
        self.Wednesday_label.setText(_translate("Widget", "Wednesday"))
        self.Tuesday_label.setText(_translate("Widget", "Tuesday"))
        self.Saturday_label.setText(_translate("Widget", "Saturday"))
        self.Thursday_label.setText(_translate("Widget", "Thursday"))
        self.Friday_label.setText(_translate("Widget", "Friday"))
        self.Working_hours_label.setText(_translate("Widget", "Working hours"))
        self.Reset.setText(_translate("Widget", "Reset"))
        self.Save.setText(_translate("Widget", "Save"))
        self.Sunday_label_2.setText(_translate("Widget", "Sunday"))
        self.Schedule_label_2.setText(_translate("Widget", "Version & update"))
        self.version_details.setText(_translate("Widget", "Application version: 2.0.0"))

    def add_dynamic_blocks(self):
        current_utc_date = datetime.utcnow().date()
        start_time_utc = datetime(current_utc_date.year, current_utc_date.month, current_utc_date.day)
        end_time_utc = start_time_utc + timedelta(days=1) - timedelta(seconds=1)
        self.refreshData()

    def refreshData(self):
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        self.displayed_events.clear()

        current_utc_date = datetime.utcnow().date()
        start_time_utc = datetime(current_utc_date.year, current_utc_date.month, current_utc_date.day)
        end_time_utc = start_time_utc + timedelta(days=1) - timedelta(seconds=1)
        events = requests.get(host + f"/0/dashboard/events?start={start_time_utc}&end={end_time_utc}")
        event = events.json()
        if event and len(event) > 0:
            listView(event['events'])
            self.layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
            for event in list_view_events:
                event_id = event['app'] + event['time']
                if event_id not in self.displayed_events:
                    color = get_next_color()
                    event_details = QtWidgets.QWidget(parent=self.scrollAreaWidgetContents)
                    event_details.setFixedSize(820, 60)
                    event_details.setStyleSheet(f"""
                        QWidget {{
                            background-color: {color};
                            border-radius: 4px;
                            margin-left: 20px;
                            margin-top: 2px;
                            margin-bottom: 10px;
                        }}
                    """)

                    application_name = QtWidgets.QLabel(parent=event_details)
                    application_name.setGeometry(QtCore.QRect(17, 15, 500, 30))
                    font = QtGui.QFont()
                    font.setPointSize(14)
                    application_name.setFont(font)
                    maxWords = 20
                    words = event['app'].split()
                    if len(words) > maxWords:
                        truncated_text = '-'.join(words[:maxWords]) + ' ...'
                    else:
                        truncated_text = event['app']
                    application_name.setText(truncated_text)
                    if len(truncated_text) > 15:
                        application_name.setToolTip(event['app'])
                        application_name.setStyleSheet("""
                            QLabel {
                                color: black;
                            }
                            QLabel::tooltip {
                                background-color: yellow;
                                color: black;
                                border: 1px solid black;
                                border-radius: 5px;
                                padding: 5px;
                                font-size: 12px;
                            }
                        """)

                    time = QtWidgets.QLabel(parent=event_details)
                    time.setGeometry(QtCore.QRect(650, 15, 251, 30))
                    time.setFont(font)
                    time.setText(event['time'])

                    self.layout.addWidget(event_details)
                    self.displayed_events.add(event_id)
        else:
            print("No events found")

    def launchOnStart(self):
        if self.startup_checkbox.isChecked():
            if sys.platform == 'darwin':
                launch_app()
            elif sys.platform == 'win32':
                set_autostart_registry(True)
        else:
            if sys.platform == 'darwin':
                delete_launch_app()
            elif sys.platform == 'win32':
                set_autostart_registry(False)
        add_settings("launch", self.startup_checkbox.isChecked())

    def update_week_schedule(self):
        week_schedule['Monday'] = self.monday_checkbox.isChecked()
        week_schedule['Tuesday'] = self.Tuesday_checkbox.isChecked()
        week_schedule['Wednesday'] = self.Wednesday_checkBox.isChecked()
        week_schedule['Thursday'] = self.Thursday_checkbox.isChecked()
        week_schedule['Friday'] = self.Friday_checkBox.isChecked()
        week_schedule['Saturday'] = self.saturday_checkBox.isChecked()
        week_schedule['Sunday'] = self.Sunday_checkBox.isChecked()

    def compare_times(self):
        from_time = self.From_time.time()
        to_time = self.To_time.time()
        if from_time > to_time:
            self.result_label.setText("From Time is greater than To Time")
        else:
            week_schedule['starttime'] = self.From_time.time().toString("h:mm AP")
            week_schedule['endtime'] = self.To_time.time().toString("h:mm AP")

    def saveSchedule(self):
        global week_schedule
        add_settings('weekdays_schedule', week_schedule)
        self.updateCheckboxStates()

    def resetSchedule(self):
        global week_schedule
        add_settings('weekdays_schedule', default_week_schedule)
        self.updateCheckboxStates()

    def updateCheckboxStates(self):
        global settings
        retrieve_settings()
        self.monday_checkbox.setChecked(settings['weekdays_schedule']['Monday'])
        self.Tuesday_checkbox.setChecked(settings['weekdays_schedule']['Tuesday'])
        self.Wednesday_checkBox.setChecked(settings['weekdays_schedule']['Wednesday'])
        self.Thursday_checkbox.setChecked(settings['weekdays_schedule']['Thursday'])
        self.Friday_checkBox.setChecked(settings['weekdays_schedule']['Friday'])
        self.saturday_checkBox.setChecked(settings['weekdays_schedule']['Saturday'])
        self.Sunday_checkBox.setChecked(settings['weekdays_schedule']['Sunday'])
        self.From_time.setTime(QtCore.QTime.fromString(settings['weekdays_schedule']['starttime'], "h:mm AP"))
        self.To_time.setTime(QtCore.QTime.fromString(settings['weekdays_schedule']['endtime'], "h:mm AP"))

    def enable_idleTime(self):
        idletime()

    def sign_out(self):
        global sundial_widget
        from sd_core.util import stop_all_module
        stop_all_module()
        delete_password("SD_KEYS")
        clear_all_credentials()
        self.reset_signin_ui()  # Reset the sign-in UI
        initialize_main_widget()
        self.bring_to_front()

    def reset_signin_ui(self):
        global signin_ui
        if signin_ui:
            for i in reversed(range(signin_ui.horizontalLayout.count())):
                widget = signin_ui.horizontalLayout.itemAt(i).widget()
                if widget is not None:
                    widget.setParent(None)
            signin_ui.setupUi(signin_widget)


class Signin(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(Signin, self).__init__(parent)
        self.setupUi(self)

    def setupUi(self, Widget):
        Widget.resize(900, 700)
        Widget.setMinimumSize(QtCore.QSize(900, 700))
        Widget.setMaximumSize(QtCore.QSize(900, 700))
        Widget.setStyleSheet("background-color: rgb(255, 255, 255);")

        if Widget.layout() is not None:
            old_layout = Widget.layout()
            while old_layout.count():
                item = old_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
            QtWidgets.QWidget().setLayout(old_layout)

        self.horizontalLayout = QtWidgets.QHBoxLayout(Widget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")

        self.widget = QtWidgets.QWidget(parent=Widget)
        self.widget.setStyleSheet(f"background-image: url({folder_path}/BackgroundImage.svg);")
        self.widget.setObjectName("widget")

        self.label = QtWidgets.QLabel(parent=self.widget)
        self.label.setGeometry(QtCore.QRect(308, 40, 291, 101))
        self.label.setStyleSheet(
            f"background-image: url({folder_path}/TTim.svg);\nbackground-repeat: none;\nbackground-color: transparent;")
        self.label.setText("")
        self.label.setObjectName("label")

        self.label_2 = QtWidgets.QLabel(parent=self.widget)
        self.label_2.setGeometry(QtCore.QRect(174, 160, 550, 124))
        self.label_2.setStyleSheet(
            f"background-image: url({folder_path}/Unleash the Power.svg);\nbackground-repeat: none;\nbackground-color: transparent;")
        self.label_2.setText("")
        self.label_2.setObjectName("label_2")

        self.label_3 = QtWidgets.QLabel(parent=self.widget)
        self.label_3.setGeometry(QtCore.QRect(240, 340, 480, 16))
        font = QtGui.QFont()
        font.setPointSize(18)
        self.label_3.setFont(font)
        self.label_3.setStyleSheet("background-repeat: none;\nbackground: transparent;")
        self.label_3.setObjectName("label_3")

        self.signIn = QtWidgets.QPushButton(parent=self.widget)
        self.signIn.setGeometry(QtCore.QRect(183, 430, 534, 64))
        self.signIn.setStyleSheet(
            "border:none;\nbackground: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #1D0B77, stop:1 #6A5FA2);\ncolor:#ffffff;\nborder-radius: 10px;")
        self.signIn.setObjectName("pushButton")
        self.signIn.clicked.connect(self.userLogin)

        self.horizontalLayout.addWidget(self.widget)

        self.retranslateUi(Widget)
        QtCore.QMetaObject.connectSlotsByName(Widget)

    def retranslateUi(self, Widget):
        _translate = QtCore.QCoreApplication.translate
        Widget.setWindowTitle(_translate("Widget", "TTim"))
        self.label_3.setText(_translate("Widget", "Automated, AI-driven time tracking software of the future"))
        self.signIn.setText(_translate("Widget", "Sign in"))

    def userLogin(self):
        self.switch_to_redirect()

    def switch_to_redirect(self):
        self.redirect_widget = QtWidgets.QWidget()
        self.redirect_ui = Redirect()
        self.redirect_ui.setupUi(self.redirect_widget)

        for i in reversed(range(self.horizontalLayout.count())):
            self.horizontalLayout.itemAt(i).widget().setParent(None)

        self.horizontalLayout.addWidget(self.redirect_widget)

    def bring_to_front(self):
        self.show()
        self.raise_()
        self.activateWindow()


class Redirect(QtWidgets.QWidget):
    api_request_completed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def setupUi(self, Widget):
        Widget.setObjectName("Widget")
        Widget.resize(900, 700)
        Widget.setMinimumSize(QtCore.QSize(900, 700))
        Widget.setMaximumSize(QtCore.QSize(900, 700))
        Widget.setStyleSheet("background-color: rgb(255, 255, 255);")

        self.horizontalLayout = QtWidgets.QHBoxLayout(Widget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")

        self.widget = QtWidgets.QWidget(parent=Widget)
        self.widget.setObjectName("widget")
        self.widget.setStyleSheet(f"background-image: url({folder_path}/BackgroundImage.svg);")

        self.Info = QtWidgets.QLabel(parent=self.widget)
        self.Info.setGeometry(QtCore.QRect(300, 360, 351, 23))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.Info.setFont(font)
        self.Info.setStyleSheet("background: transparent;")
        self.Info.setObjectName("Info")

        self.Button = QtWidgets.QPushButton(parent=self.widget)
        self.Button.setGeometry(QtCore.QRect(183, 431, 534, 64))
        self.Button.setObjectName("Button")
        self.Button.setStyleSheet(
            "border:none;\nbackground: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #1D0B77, stop:1 #6A5FA2);\ncolor:#ffffff;\nborder-radius: 10px;")
        self.Button.clicked.connect(self.redirect_url)

        self.Icon = QtWidgets.QLabel(parent=self.widget)
        self.Icon.setGeometry(QtCore.QRect(397, 206, 160, 154))
        self.Icon.setText("")
        self.Icon.setObjectName("Icon")

        pixmap = QtGui.QPixmap(folder_path + '/RedirectImage.png')
        scaled_pixmap = pixmap.scaled(106, 102, QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                                      QtCore.Qt.TransformationMode.SmoothTransformation)

        self.Icon.setPixmap(scaled_pixmap)
        self.Icon.setStyleSheet("background-repeat: no-repeat;\nbackground-color: transparent;\nbackground:none;")

        self.horizontalLayout.addWidget(self.widget)

        self.retranslateUi(Widget)
        QtCore.QMetaObject.connectSlotsByName(Widget)
        self.start_api_request()

    def retranslateUi(self, Widget):
        _translate = QtCore.QCoreApplication.translate
        Widget.setWindowTitle(_translate("Widget", "Widget"))
        self.Info.setText(_translate("Widget", "Please continue to authorize in the browser."))
        self.Button.setText(_translate("Widget", "Sign in with browser"))

    def redirect_url(self):
        global URI
        webbrowser.open(URI)

    def start_api_request(self):
        threading.Thread(target=self.api_request).start()

    def api_request(self):
        from sd_datastore.storages.peewee import PeeweeStorage
        from sd_core.util import encrypt_uuid
        global URI
        user_credentials = None
        peewee = PeeweeStorage()
        unique_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        URI = f"http://14.97.160.178:9011/sunidal-authentication/?code={unique_code}"
        webbrowser.open(URI)
        data_request_URI = f"http://14.97.160.178:9010/api/v1/users/{unique_code}/sundial_auth"
        while not user_credentials:
            user_credentials = requests.get(data_request_URI)
            if user_credentials.status_code == 200 and json.loads(user_credentials.text)["code"] == 'RCI0000':
                credentials_data = json.loads(user_credentials.text)["data"]["credentials"]
                user_data = json.loads(user_credentials.text)["data"]
                data=user_data
                db_key = credentials_data["dbKey"]
                userId = json.loads(user_credentials.text)["data"]['id']
                data_encryption_key = credentials_data["dataEncryptionKey"]
                user_key = credentials_data["userKey"]
                email = user_data.get("email", None)
                phone = user_data.get("phone", None)
                companyId = user_data.get("companyId", None)
                firstName = user_data.get("firstName", None)
                lastName = user_data.get("lastName", None)
                key = user_key
                encrypted_db_key = encrypt_uuid(db_key, key)
                encrypted_data_encryption_key = encrypt_uuid(data_encryption_key, key)
                encrypted_user_key = encrypt_uuid(user_key, key)

                SD_KEYS = {
                    "userId": userId,
                    "user_key": user_key,
                    "encrypted_db_key": encrypted_db_key,
                    "encrypted_data_encryption_key": encrypted_data_encryption_key,
                    "email": email,
                    "phone": phone,
                    "firstname": firstName,
                    "lastname" : lastName,
                    "companyId": companyId,
                }

                store_credentials("Sundial", SD_KEYS)
                serialized_data = json.dumps(SD_KEYS)
                add_password("SD_KEYS", serialized_data)

                cached_credentials = get_credentials("Sundial")
                key_decoded = cached_credentials.get("user_key")
                requests.get(host + "/0/init_db")

                self.api_request_completed.emit()
                break
            else:
                user_credentials = None
                time.sleep(2)


    def retranslateUi(self, Widget):
        _translate = QtCore.QCoreApplication.translate
        Widget.setWindowTitle(_translate("Widget", "Widget"))
        self.Info.setText(_translate("Widget", "Please continue to authorize in the browser."))
        self.Button.setText(_translate("Widget", "Sign in with browser"))

    def redirect_url(self):
        global URI
        webbrowser.open(URI)


def retrieve_settings():
    global settings
    sett = requests.get("http://localhost:7600/api/0/getallsettings")
    settings = sett.json()
    return settings


def listView(events):
    global list_view_events
    list_view_events.clear()

    local_tz = datetime.now().astimezone().tzinfo

    for event in events:
        start_time_utc = datetime.strptime(event['start'], "%Y-%m-%dT%H:%M:%SZ")
        end_time_utc = datetime.strptime(event['end'], "%Y-%m-%dT%H:%M:%SZ")

        start_time_local = start_time_utc.replace(tzinfo=pytz.utc).astimezone(local_tz).strftime("%H:%M:%S")
        end_time_local = end_time_utc.replace(tzinfo=pytz.utc).astimezone(local_tz).strftime("%H:%M:%S")

        formatted_event = {
            'time': f"{start_time_local} - {end_time_local}",
            'app': event['title']
        }
        list_view_events.append(formatted_event)


def add_settings(key, value):
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    data = json.dumps({"code": key, "value": value})
    response = requests.post(host + "/0/settings", data=data, headers=headers)
    print(response.json())
    retrieve_settings()


def get_next_color():
    global current_color_index
    current_color_index = (current_color_index + 1) % len(colors)
    return colors[current_color_index]


def user_details():
    global userdetails
    cache_key = "Sundial"
    cached_credentials = get_credentials(cache_key)
    userdetails['firstname'] = cached_credentials['firstname']
    userdetails['lastname'] = cached_credentials['lastname']
    userdetails['phone'] = cached_credentials['phone']
    userdetails['email'] = cached_credentials['email']


def get_user_details():
    global first_name, settings
    cache_key = "Sundial"
    cached_credentials = get_credentials(cache_key)
    first_name = cached_credentials.get('firstname')
    retrieve_settings()


def idletime():
    from sd_qt.manager import Manager
    manager = Manager()
    module = manager.module_status("sd-watcher-afk")
    if module["is_alive"]:
        manager.stop("sd-watcher-afk")
        state = False
    else:
        manager.start("sd-watcher-afk")
        state = True
    add_settings('idletime', state)


def setup_sundial(main_widget):
    global sundial_widget
    sundial_widget = Sundial()
    sundial_widget.setupUi(main_widget)
    return sundial_widget


def setup_signin(main_widget, switch_to_sundial):
    signin_widget = Signin()
    signin_widget.setupUi(main_widget)
    credentials_timer = QTimer()

    def on_signin():
        signin_widget.switch_to_redirect()
        credentials_timer.timeout.connect(check_credentials)
        credentials_timer.start(5000)
        signin_ui.bring_to_front()

    def check_credentials():
        credentials = check_user_credentials()
        if credentials:
            switch_to_sundial()
            credentials_timer.stop()
        else:
            print("Authentication failed")

    signin_widget.signIn.clicked.connect(on_signin)
    return signin_widget


def setup_tray_icon(main_widget, icon_path):
    tray_icon = TrayIcon(icon_path, main_widget)
    tray_icon.show()
    return tray_icon


def load_credentials(cache_key):
    try:
        return cache_user_credentials(cache_key, "SD_KEYS")
    except Exception as e:
        print(f"Failed to retrieve credentials: {e}")
        return None


def check_user_credentials():
    return cache_user_credentials("Sundial", "SD_KEYS")


def switch_to_sundial():
    if signin_widget.isVisible():
        signin_widget.close()
    sundial_ui = Sundial()
    sundial_ui.setupUi(sundial_widget)
    tray_icon.update_parent(sundial_widget)
    sundial_ui.bring_to_front()
    sundial_widget.show()
    sundial_widget.raise_()
    sundial_widget.activateWindow()

def on_signin():
    global credentials_timer
    credentials_timer = QTimer()
    signin_ui.switch_to_redirect()
    credentials_timer.timeout.connect(check_credentials)
    credentials_timer.start(5000)

def check_credentials():
    credentials = check_user_credentials()
    if credentials:
        credentials_timer.stop()
        switch_to_sundial()
    else:
        print("Authentication failed")

def initialize_main_widget():
    cache_key = "Sundial"
    cached_credentials = load_credentials(cache_key)
    if cached_credentials:
        switch_to_sundial()
        return sundial_widget
    else:
        if sundial_widget.isVisible():
            sundial_widget.close()
        global signin_ui  # Ensure signin_ui is accessible globally
        signin_ui = Signin()
        signin_ui.setupUi(signin_widget)
        signin_ui.signIn.clicked.connect(on_signin)
        tray_icon.update_parent(signin_widget)
        signin_widget.show()
        signin_widget.raise_()
        signin_widget.activateWindow()
        return signin_widget



def run_application():
    global sundial_widget, tray_icon, signin_widget

    app = QApplication(sys.argv)
    QApplication.setStyle('Fusion')
    scriptdir = Path(__file__).parent.parent
    print(scriptdir)
    # When run from source:
    #   __file__ is aw_qt/trayicon.py
    #   scriptdir is ./aw_qt
    #   logodir is ./media/logo
    QtCore.QDir.addSearchPath("icons", str(scriptdir.parent / "media/logo/"))

    # When run from .app:
    #   __file__ is ./Contents/MacOS/aw-qt
    #   scriptdir is ./Contents/MacOS
    #   logodir is ./Contents/Resources/aw_qt/media/logo
    QtCore.QDir.addSearchPath(
        "icons", str(scriptdir.parent.parent / "Resources/sd_qt/media/logo/")
    )


    signin_widget = QWidget()
    sundial_widget = QWidget()
    if sys.platform == "darwin":
        icon = QIcon("icons:black-monochrome-logo.png")
        # Allow macOS to use filters for changing the icon's color
        icon.setIsMask(True)
    else:
        icon = QIcon("icons:logo.png")

    tray_icon = TrayIcon(icon)

    main_widget = initialize_main_widget()

    tray_icon.update_parent(main_widget)
    tray_icon.show()

    app.setQuitOnLastWindowClosed(False)
    sys.exit(app.exec())

if __name__ == "__main__":
    run_application()

