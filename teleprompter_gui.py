from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pyqtgraph as pg
import time
from rename_files_simple import Rename
import json
from pyqt_responsive_label import ResponsiveLabel
import math 
import re 

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
        self.config_file = "config.json"

        self.layout = QVBoxLayout()
        self.width, self.height = self.getConfig()
        self.resize(self.width, self.height)

        # teleprompter label setup

        self.font = QFont()
        self.font.setPointSize(120)  

        self.label = ResponsiveLabel(self)
        self.label.setText("Waiting to start up...")

        self.label.setFont(self.font)  
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        #self.label.setMaximumWidth(1500) # this can be tweaked
        self.layout.addWidget(self.label, 1)

        # setting up the words left label

        self.wordsLeftLayout = QHBoxLayout()
        self.wordsLeftFont = QFont()
        self.wordsLeftFont.setPointSize(20)  

        self.wordsLeftLabel = QLabel("Phrases left: 0", self)
        self.wordsLeftLabel.setFont(self.wordsLeftFont)
        self.wordsLeftLabel.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.wordsLeftLayout.addStretch(1)
        self.wordsLeftLayout.addWidget(self.wordsLeftLabel)
        self.layout.addLayout(self.wordsLeftLayout)

        # setting up estimated time remaining label

        self.timeLeftLayout = QHBoxLayout()
        self.timeLeftFont = QFont()
        self.timeLeftFont.setPointSize(20)  

        self.timeLeftLabel = QLabel(f"Time Remaining: 0m 0s", self)
        self.timeLeftLabel.setFont(self.wordsLeftFont)
        self.timeLeftLabel.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.timeLeftLayout.addStretch(1)
        self.timeLeftLayout.addWidget(self.timeLeftLabel)
        self.layout.addLayout(self.timeLeftLayout)

        self.recordLength = 3 # will be changed based on the radio buttons the user clicks

        # radio buttons setup

        self.radio_button_layout = QHBoxLayout()

        self.recLengthLabel = QLabel("Recording Length (Seconds):", self)
        self.radio_button_layout.addWidget(self.recLengthLabel)

        self.oneRadioButton = QRadioButton("1")
        self.oneRadioButton.toggled.connect(lambda checked: self.set_recording_length(1) if checked else None)
        self.radio_button_layout.addWidget(self.oneRadioButton)

        self.twoRadioButton = QRadioButton("2")
        self.twoRadioButton.toggled.connect(lambda checked: self.set_recording_length(2) if checked else None)
        self.radio_button_layout.addWidget(self.twoRadioButton)

        self.threeRadioButton = QRadioButton("3")
        self.threeRadioButton.setChecked(True)
        self.threeRadioButton.toggled.connect(lambda checked: self.set_recording_length(3) if checked else None)
        self.radio_button_layout.addWidget(self.threeRadioButton)

        self.fiveRadioButton = QRadioButton("5")
        self.fiveRadioButton.toggled.connect(lambda checked: self.set_recording_length(5) if checked else None)
        self.radio_button_layout.addWidget(self.fiveRadioButton)

        self.autoRadioButton = QRadioButton("Auto")
        self.autoRadioButton.toggled.connect(lambda checked: self.set_recording_length_auto(99) if checked else None)
        self.radio_button_layout.addWidget(self.autoRadioButton)

        self.layout.addLayout(self.radio_button_layout)

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

    def getConfig(self):
        # Try to read the saved dimensions from the config file
        try:
            with open(self.config_file, 'r') as file:
                config = json.load(file)
                return [config.get('width', 750), config.get('height', 750)]
        except (FileNotFoundError, json.JSONDecodeError):
            return [750, 750]  # Return default dimensions if there's an issue reading the file

    def resizeEvent(self, event):
        # Save the new dimensions to the config file whenever the window is resized
        newSize = event.size()
        config = {'width': newSize.width(), 'height': newSize.height()}
        with open(self.config_file, 'w') as file:
            json.dump(config, file)
        super().resizeEvent(event)

    def show_word(self, x):
        """sets the label to the input, x, provided"""
        self.label.setText(str(x))

    def change_words_left(self, x):
        """changes the words left label"""
        self.wordsLeftLabel.setText("Phrases Left: " + str(x))

    def set_recording_length(self, x):
        self.recordLength = x

    def set_recording_length_auto(self, x):
        self.recordLength = x



    def toggle_radio_buttons(self):
        state = not self.oneRadioButton.isEnabled()
        self.oneRadioButton.setEnabled(state)
        self.twoRadioButton.setEnabled(state)
        self.threeRadioButton.setEnabled(state)
        self.fiveRadioButton.setEnabled(state)
    
    def get_recording_length(self):
        return self.recordLength

    def start_stop_experiment(self):
        self.start_stop_experiment_signal.emit()

    def change_time_remaining(self, x):
        """changes the time remaining label"""
        self.timeLeftLabel.setText("Time Remaining: " + str(x))
    
class tpThread(QThread):

    start_stop_signal = pyqtSignal()

    def __init__(self):
        QThread.__init__(self)
        self.counter = 0
        self.wait_period_after = 1
        self.wait_period_before = 0
        self.current_word = 0
        self.iterations = 1 # number of times we want to display each phrase - can make this selectable later
        self.seen_words = {} # dictionary to keep track of which words have already been displayed and when they were displayed
        self.is_repeated = False
        self.rename_emg = Rename()
        self.rename_audio = Rename()

        # state variable to keep track where we are:
        # 0 = waiting/not running
        # 1 = running/countdown
        # 2 = running/show_word
        # 3 = running/countdown
        # 4 = finish/back_to_start
            # if finished, calls the start_stop_experiment() method
            # if back_to_start, calls the next_word() method
        
        self.running_experiment = 0

        self.time_remaining = 0

        self.running = 0
        #make window

        # eventually make utterances selectable
        self.file_path = './utterances.txt'
        self.words = self.extract_phrases()

        self.teleprompter = teleprompter()
        self.teleprompter.startStopButton.clicked.connect(self.start_stop_experiment)
        self.record_period = self.teleprompter.get_recording_length() # selectable, 2s 3s, 5s
        
        #self.teleprompter.start_stop_experiment_signal.connect(self.start_stop_experiment)

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

    def calculate_recording_duration(self, sentence, words_per_second=1):
        """
        Calculate recording duration based on the number of words.
        
        Args:
            sentence (str): The sentence to be recorded.
            words_per_second (float): Estimated speaking rate.
        
        Returns:
            float: Duration in seconds.
        """
        word_count = len(sentence.split())
        base_duration = round(word_count / words_per_second)
        
        # Define pause durations for punctuation
        comma_pause = 0.5  # seconds per comma
        period_pause = 1.0  # seconds per period, question mark, exclamation mark

        # Count punctuation
        comma_count = len(re.findall(r',', sentence))
        period_count = len(re.findall(r'[.!?]', sentence))

        # Calculate total pause duration
        total_pause_duration = (comma_count * comma_pause) + (period_count * period_pause)

        # Total duration
        total_duration = round(base_duration + total_pause_duration)

        # Set minimum and maximum duration limits
        return max(1, min(total_duration, 60))  # For example, between 1 and 60 seconds

    @pyqtSlot()
    def start_stop_experiment(self):
        if (self.running_experiment == 0):

            # set recording length using radio buttons and freeze radio buttons
            self.record_period = self.teleprompter.get_recording_length()
            self.teleprompter.toggle_radio_buttons()

            if self.record_period == 99: # dynamic recording length
                for phrase in self.words:
                    duration = self.calculate_recording_duration(phrase)
                    self.time_remaining += duration + self.wait_period_after + self.wait_period_before
            else:
                # each word has a wait before, recording time, and a wait after
                self.total_recording_length = self.record_period + self.wait_period_after + self.wait_period_before

                # we also add 3 seconds per word
                wand_wait_time = 3 * self.total_recording_length

                self.time_remaining = self.total_recording_length * len(self.words)

            self.running_experiment = 1
            self.update_graphic("starting up...")

            self.stream() # start streaming
        else:
            self.running_experiment = 0
            self.current_word = 0
            self.counter = 0

            self.stream() # stop streaming

            time.sleep(1)
        
            # open radio buttons back up
            self.teleprompter.toggle_radio_buttons()
    
    def update_graphic(self,text):
        self.teleprompter.show_word(text)

    def next_word(self):
        if (self.running_experiment == 0):
            self.running_experiment = 1
            self.stream() # stop streaming
        else:
            self.running_experiment = 0
            self.stream() # stop streaming

    def is_word_repeated(self, word, timestamp, grace_period=2):
        if word in self.seen_words:
            if timestamp - self.seen_words[word] <= grace_period:
                return False
            else:
                self.seen_words[word] = timestamp
                return True
        else:
            self.seen_words[word] = timestamp
            return False
    
    def update_graphic(self,text):
        self.teleprompter.show_word(text)

    def update_words_left(self, text):
        self.teleprompter.change_words_left(str(text))

    def display_time_remaining(self, seconds):
        minutes = seconds // 60
        remaining_seconds = seconds % 60

        return f"{minutes}m {remaining_seconds}s"

    def update_time_remaining(self, text):
        self.teleprompter.change_time_remaining(str(text))


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

            if self.wait_period_before == 0: 
                self.update_words_left(len(self.words) - self.current_word)
                self.running_experiment = 2
                self.counter = 0
            else:
                # change background back to gray
                self.teleprompter.setStyleSheet("")

                self.update_graphic("next phrase...")
                self.update_words_left(len(self.words) - self.current_word)
                self.counter += 1
                self.time_remaining = self.time_remaining - 1
                self.update_time_remaining(self.display_time_remaining(self.time_remaining))
            

                if self.counter == self.wait_period_before:
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
            
            # Calculate dynamic recording duration
            if self.record_period == 99:
                self.recording_time = self.calculate_recording_duration(phrase)
                print(self.recording_time)
            else:
                self.recording_time = self.record_period

            self.counter += 1
            self.time_remaining = self.time_remaining - 1
            self.update_time_remaining(self.display_time_remaining(self.time_remaining))
            
            if self.counter == self.recording_time:
                #update state variable
                self.counter = 0
                self.running_experiment = 3


        elif self.running_experiment == 3:
            ## running/countdown_after
            
            # currently waiting 0 seconds - show no countdown after word

            if self.wait_period_after == 0:
                self.counter = 0
                self.running_experiment = 4
            else:
                # change background back to grey
                self.teleprompter.setStyleSheet("")
                self.update_graphic("next phrase...")
                self.counter += 1
                self.time_remaining = self.time_remaining - 1
                self.update_time_remaining(self.display_time_remaining(self.time_remaining))
                
                #action
                if self.counter == self.wait_period_after:
                    ## update state variable
                    self.counter = 0
                    self.running_experiment = 4

        elif self.running_experiment == 4:
            ## finish/back_to_start

            to_rename = self.words[self.current_word]

            #action
            if self.current_word < len(self.words) - 1:
                self.stream() # stop streaming
                time.sleep(1)  # Wait for 1 sec before starting a new cycle

                self.current_word += 1 
                self.reset()
            else:
                self.teleprompter.setStyleSheet("background-color: #4CAF50")
                self.update_words_left(0)
                self.update_graphic("Done")
                print("All phrases displayed.")
                self.start_stop_experiment()

            # renames the first audio and emg file that hasn't been renamed yet ie the file for this current phrase
            self.rename_audio.rename_file(to_rename, "audio", "wav", self.current_word + 1)
            self.rename_emg.rename_file(to_rename, "data", "mat", self.current_word + 1)
                

    def reset(self):
        self.running_experiment = 0
        self.counter = 0
        self.next_word()