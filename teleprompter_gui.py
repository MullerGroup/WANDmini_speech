from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pyqtgraph as pg
import time
from rename_files import Rename

class teleprompter(QWidget):
    """
    This "window" is a QWidget, it has no parent and will be a free floating separate window!
    """

    start_stop_experiment_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        
        self.initGUI()

    def initGUI(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.show_word)

        self.layout = QVBoxLayout()
        self.resize(750, 750)

        # teleprompter label setup

        self.font = QFont()
        self.font.setPointSize(150)  

        self.label = QLabel("Waiting to start up...", self)
        self.label.setFont(self.font)  
        self.label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label)

        # teleprompter buttons setup

        self.startStopButton = QPushButton('Start/Stop Experiment', self)
        self.layout.addWidget(self.startStopButton)

        self.setLayout(self.layout)
        self.setWindowTitle('Teleprompter')

        # This line ensures the window can go full screen and back.
        self.setWindowFlags(Qt.Window | Qt.WindowSystemMenuHint | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)

    def toggleFullScreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def show_word(self, x):
        """sets the label to the input, x, provided"""
        self.label.setText(str(x))

    def start_stop_experiment(self):
        self.start_stop_experiment_signal.emit()
    

class tpThread(QThread):

    start_stop_signal = pyqtSignal()

    def __init__(self):
        QThread.__init__(self)
        self.counter = 0
        self.wait_period = 3
        self.max_count = 2
        self.current_word = 0
        self.iterations = 1 # number of times we want to display each phrase - can make this selectable later

        # state variable to keep track where we are:
        # 0 = waiting/not running
        # 1 = running/countdown
        # 2 = running/show_word
        # 3 = running/countdown
        # 4 = finish/back_to_start
            # if finished, calls the start_stop_experiment() method
            # if back_to_start, calls the next_word() method
        
        self.running_experiment = 0

        self.running = 0
        #make window

        # eventually make utterances selectable
        self.file_path = './utterances.txt'
        self.words = self.extract_phrases()

        self.teleprompter = teleprompter()
        self.teleprompter.startStopButton.clicked.connect(self.start_stop_experiment)
        #self.teleprompter.start_stop_experiment_signal.connect(self.start_stop_experiment)

        # connect signals

    def extract_phrases(self):
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
    def start_stop_experiment(self):
        if (self.running_experiment == 0):
            self.running_experiment = 1
            self.update_graphic("starting up...")
            self.stream()
        else:
            self.running_experiment = 0
            self.current_word = 0
            self.counter = 0
            self.stream()

            time.sleep(1)

            # call the script to rename files
            rename = Rename()
            rename.rename_files()
    
    def update_graphic(self,text):
        self.teleprompter.show_word(text)

    def next_word(self):
        if (self.running_experiment == 0):
            self.running_experiment = 1
            self.stream()
        else:
            self.running_experiment = 0
            self.stream()
    
    def update_graphic(self,text):
        self.teleprompter.show_word(text)


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

        # if experiment has not started, running_experiment = 0
        # if experiment is running, running_experiment = 1
        # if experiment has finished for this set of phrases, running_experiment = 2

        if self.running_experiment == 0:
            ## what do we do here?
            pass

            #action

            #update state variable
        elif self.running_experiment == 1:
            ## running/countdown_before

            # change background back to gray
            self.teleprompter.setStyleSheet("")

            #action
            self.update_graphic(self.wait_period - self.counter)
            self.counter += 1

            if self.counter == self.wait_period:
                #update state variable
                self.running_experiment = 2
                self.counter = 0
                
        elif self.running_experiment == 2:
            ## running/show_word

            #action

            #change background to green

            self.teleprompter.setStyleSheet("background-color: #4CAF50")

            phrase = self.words[self.current_word]
            self.update_graphic(phrase)
            self.counter += 1

            if self.counter == self.max_count:
                #update state variable
                self.counter = 0
                self.running_experiment = 3


        elif self.running_experiment == 3:
            ## running/countdown_after

            # change background back to grey
            self.teleprompter.setStyleSheet("")

            if (self.wait_period - self.counter) == 1:
                self.update_graphic("next word...")
            else:
                self.update_graphic(self.wait_period - self.counter)
            
            self.counter += 1

            #action
            if self.counter == self.wait_period:
                ## update state variable
                self.counter = 0
                self.running_experiment = 4
    
        elif self.running_experiment == 4:
            ## finish/back_to_start

            #action
            if self.current_word < len(self.words) - 1:
                self.stream() # stop streaming
                time.sleep(1)  # Wait for 1 sec before starting a new cycle
                self.current_word += 1 
                self.reset()
            else:
                self.teleprompter.setStyleSheet("background-color: #4CAF50")
                self.update_graphic("Done")
                print("All phrases displayed.")
                self.start_stop_experiment()
                

    def reset(self):
        self.running_experiment = 0
        self.counter = 0
        self.next_word()