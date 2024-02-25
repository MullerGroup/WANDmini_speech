import sys
import wave
import pyaudio
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout
from PyQt5.QtCore import QThread, pyqtSignal
import datetime

class AudioRecorder(QThread):
    def __init__(self):
        super().__init__()
        self.running = False  # Controls the recording loop.

    def run(self):
        self.running = True

        # configuring the audio recording
        # -- chunk defines the number of audio samples taken at a time, 
        # -- sample format specifies the audio sample format, not sure what different choices we have here
        # -- channels is set to 1 for mono recording, as stereo is not supported on some hardware (my mac).
        # -- fs is the sampling rate, the average number of samples obtained in one second

        chunk = 1024  
        sample_format = pyaudio.paInt16  
        channels = 1  
        fs = 44100  

        p = pyaudio.PyAudio()  # Create an interface to PortAudio.

        try:
            # Open the stream for recording.
            stream = p.open(format=sample_format,
                            channels=channels,
                            rate=fs,
                            frames_per_buffer=chunk,
                            input=True)

            frames = []  # Initialize array to store frames.

            # Record audio in chunks until recording is stopped.
            while self.running:
                data = stream.read(chunk)
                frames.append(data)

            # Properly close the stream and terminate PyAudio.
            stream.stop_stream()
            stream.close()
            p.terminate()

            # Save the recorded data as a WAV file. need to join all the frames together
            saveDir = './audio/'
            outputFileName = datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + '.wav'
            wf = wave.open(saveDir + outputFileName, 'wb')
            wf.setnchannels(channels)
            wf.setsampwidth(p.get_sample_size(sample_format))
            wf.setframerate(fs)
            wf.writeframes(b''.join(frames))
            wf.close()
        except Exception as e:
            print(f"An error occurred: {e}")           

    def stop(self):
        # Stop the recording loop.
        self.running = False