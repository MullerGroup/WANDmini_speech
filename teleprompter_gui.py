from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pyqtgraph as pg
import time 

class teleprompter(QWidget):
    """
    This "window" is a QWidget, it has no parent and will be a free floating seperate window!
    """

    start_stop_experiment_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        
        self.initGUI()


    def initGUI(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.show_word)

        self.layout = QVBoxLayout()
        self.setFixedWidth(500)  
        self.setFixedHeight(500)  

        # teleprompter label setup

        font = QFont()
        font.setPointSize(25)  

        self.label = QLabel("Waiting to start up...", self)
        self.label.setFont(font)  
        self.label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label)

        # teleprompter buttons setup

        # need to implement pause and reset functionality such that it works with the pyqt thread

        self.startStopButton = QPushButton('Start/Stop Experiment', self)
        self.startStopButton.clicked.connect(self.start_stop_experiment)
        self.layout.addWidget(self.startStopButton)

        self.setLayout(self.layout)
        self.setWindowTitle('Teleprompter')

    def show_word(self, x):
        """sets the label to the input, x, provided"""
        self.label.setText(str(x))

    def start_stop_experiment(self):
        self.start_stop_experiment_signal.emit()
    

class tpThread(QThread):

    start_stop_signal = pyqtSignal()

    def __init__(self):
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
        self.running_experiment = 0

        self.running = 0
        #make window

        # eventually make utterances selectable
        self.file_path = './utterances.txt'
        self.words = self.extract_phrases()

        self.teleprompter = teleprompter()

        self.teleprompter.start_stop_experiment_signal.connect(self.start_stop_experiment)

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
            self.update_graphic(self.wait_period)
            self.stream()
        elif self.running_experiment == 1:
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
            print("state 0")

            #action

            #update state variable
        elif self.running_experiment == 1:
            ## running/countdown_before
            print("state 1")
            self.counter = 0

            #action
            if self.counter == self.wait_period:
                #update state variable
                self.running_experiment = 2
            else:
                self.update_graphic(self.wait_period - self.counter)
                self.counter += 1

        elif self.running_experiment == 2:
            ## running/show_word
            print("state 2")
            self.counter = 0

            #action
            
            phrase = self.words[self.current_word]
            self.update_graphic(phrase)

            if self.counter == self.max_count:
                #update state variable
                self.running_experiment = 3
            else:
                self.counter += 1

        elif self.running_experiment == 3:
            ## running/countdown_after
            print("state 3")

            ## action
            self.counter = 0

            #action
            if self.counter == self.wait_period:
                ## update state variable
                self.running_experiment = 4

            else:
                self.update_graphic(self.wait_period - self.counter)
                self.counter += 1

    
        elif self.running_experiment == 4:
            ## finish/back_to_start
            print("state 4")

            #action
            if self.current_word < len(self.words):
                self.stream() # stop streaming
                time.sleep(1)  # Wait for 1 sec before starting a new cycle
                self.current_word += 1 
                reset()
            else:
                print("All phrases displayed.")
                self.update_graphic("Done")
                self.start_stop_experiment()

        """if self.running_experiment == 1:
            if self.counter == self.max_count: # checks if it has waited for max_count seconds (1 iteration completed)
                self.iterations -= 1 # the word has been displayed once
                self.wait_period = 3 # make it wait
                self.counter = 0
            else:
                if self.wait_period != 0: # still need to wait before displaying the next word
                    self.update_graphic(self.wait_period)
                    self.wait_period -= 1
                
                # if done waiting, display the next word or terminate
                else: 
                    if self.iterations == 0: # if phrase has been displayed x times, the data has been collected for that particular phrase
                        "add a line to stop streaming wandmini data"
                        self.running_experiment = 2
                    else:
                        phrase_to_display = self.words[self.current_word]
                        self.update_graphic(phrase_to_display)
                        self.counter += 1
    
        # if self.running_experiment == 2
        elif self.running_experiment == 2:
            if self.current_word < len(self.words):
                self.stream()
                time.sleep(1)  # Wait for 1 sec before starting a new cycle
                self.current_word += 1 # Move to the next phrase
                reset()
            else:
                # All phrases have been displayed
                print("All phrases displayed.")
                self.teleprompter.show_word("Done")
                self.start_stop_experiment()"""


    def reset(self):
        self.running_experiment = 0
        self.counter = 0
        self.start_stop_experiment()
    
    # def run(self):
    #     self.teleprompter.show()

    #     if not self.running:
    #         self.running = True
    #         print('Starting GUI')