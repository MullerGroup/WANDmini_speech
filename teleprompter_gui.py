from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pyqtgraph as pg

class teleprompter(QWidget):
    """
    This "window" is a QWidget, it has no parent and will be a free floating seperate window!
    """

    def __init__(self):
        super().__init__()

        self.initGUI()


    def initGUI(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.showWord)

        self.layout = QVBoxLayout()
        self.setFixedWidth(500)  
        self.setFixedHeight(500)  

        font = QFont()
        font.setPointSize(25)  

        self.label = QLabel(self.word_list[self.current_index], self)
        self.label.setFont(font)  
        self.label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label)

        self.startStopButton = QPushButton('Start', self)
        self.startStopButton.clicked.connect(self.startStopTimer)
        self.layout.addWidget(self.startStopButton)

        self.resetButton = QPushButton('Reset', self)
        self.resetButton.clicked.connect(self.resetSequence)
        self.layout.addWidget(self.resetButton)

        self.setLayout(self.layout)
        self.setWindowTitle('Teleprompter')

    def updateText(self):
        print("update shown text")


class tpThread(QThread):

    start_stop_signal = pyqtSignal()

    def __init__(self):
        self.counter = 0
        self.wait_period = 1
        self.max_count = 3

        self.running_experiment = 0

        self.running = 0
        #make window

        # eventually make utterances selectable
        self.file_path = './utterances.txt'
        self.words = self.extract_phrases(self.file_path)

        self.teleprompter = teleprompter()

        # connect signals

    def extract_phrases(self,textfile):
        try:
            with open(self.file_path, 'r') as file:
                phrases = [line.strip() for line in file if line.strip()]
            return phrases
        except FileNotFoundError:
            print(f"The file at {self.file_path} was not found.")
            return []
        except Exception as e:
            print(f"An error occurred: {e}")
            return []

    def stream(self):
        self.start_stop_signal.emit()

    @pyqtSlot()
    def update_tp(self):
        # will run once every second (according to the emit signal from the processThread)
        # update counter or phrase shown on teleprompter

        # If waiting:
        # -- Do nothing

        # If about to start (self.running_experiment = 0):
        # -- start streaming
        # -- start incrementing counter

        # If running:
        # -- increment counter
        # -- update GUI with appropriate number or phrase
        # -- check if done

        # If done:
        # -- stop streaming
        # -- if there's another word left, wait 1 sec (via time) and go back to 'about to start'
        # -- if there are no words left then stop and close
        print("got the signal!")
    
    def run(self):
        self.teleprompter.show()

        if not self.running:
            self.running = True
            print('Starting GUI')
    