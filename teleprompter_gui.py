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

        self.file_path = './utterances.txt'
        self.words = self.extract_phrases(self.file_path)
        self.current_index = 0 
        self.initGUI()


    def initGUI(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.show_word)

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

    def show_word(self):
        """returns the current word in word list"""
        self.label.setText(self.word_list[self.current_index])
    
    def hide_word(self):
        """hides text"""
        self.label.setText("")

    def updateText(self):
        # update the label on the teleprompter
        print("update shown text")


class tpThread(QThread):

    start_stop_signal = pyqtSignal()

    def __init__(self):
        self.counter = 0
        self.wait_period = 1
        self.max_count = 3
        self.current_word = 0
        self.iterations = 12 # number of times we want to display each phrase - can make this selectable later

        self.running_experiment = 0

        self.running = 0
        #make window

        # eventually make utterances selectable


        # if the section in the telepromter qwidget works, don't need these two lines
        self.file_path = './utterances.txt' 
        self.words = self.extract_phrases(self.file_path)

        self.teleprompter = teleprompter()

        # connect signals

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


        # if experiment is running, running_experiment = 1
        # if experiment has finished for this set of phrases, running_experiment = 2
        
        if self.running_experiment == 0:
            # run
            self.running_experiment = 1  
            self.stream()

        elif self.running_experiment == 1:
            
            if self.iterations == 0: # if phrase has been displayed x times, the data has been collected for that particular phrase
                self.running_experiment = 2

            if self.counter == self.max_count: # checks if it has waited for max_count seconds (1 iteration completed)
                self.teleprompter.hide_word() 
                self.iterations -= 1 # the word has been displayed once
                self.wait_period = 1
                self.counter = 0
            else:
                if self.wait_period != 0: # still need to wait before displaying the next word
                    self.wait_period -= 1
                else: # if done waiting, display the next word
                    phrase_to_display = self.words[self.current_word]
                    self.teleprompter.show_word(phrase_to_display)
                    self.counter += 1
    
        # if self.running_experiment == 2
        else:
            if self.current_word < len(self.teleprompter.words):
                # Reset for a new cycle after waiting
                self.current_word += 1 # Move to the next phrase
                QTimer.singleShot(1000, self.reset)  # Wait for 1 sec before starting a new cycle
            else:
                # All phrases have been displayed, possibly close the teleprompter
                print("All phrases displayed.")
                
                self.running_experiment = 0  # Reset everything to allow a new start
                self.counter = 0  
                self.current_word = 0

    def reset(self):
        self.running_experiment = 0
        self.update_tp()

    
    def run(self):
        self.teleprompter.show()

        if not self.running:
            self.running = True
            print('Starting GUI')
    