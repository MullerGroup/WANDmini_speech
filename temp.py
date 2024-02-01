import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pyqtgraph as pg
from queue import Queue, Empty
import WANDminiComm
import time
import numpy as np
import scipy.io as sio
import datetime
import os

# for writing stdout to text box
class StdoutHandler(QObject):
    written = pyqtSignal(str)

    def __init__(self, parent = None):
        QObject.__init__(self, parent)

    def write(self, data):
        self.written.emit(str(data))

class cp2130Thread(QThread):
    def __init__(self):
        QThread.__init__(self)
        self._running = False

    def __del__(self):
        self.wait()
    
    def stop(self):
        self._running = False

    def run(self):
        if not self._running:
            self._running = True
            WANDminiComm.cp2130_libusb_flush_radio_fifo(cp2130Handle)
            sampleQueue.queue.clear()
            time.sleep(0.1)
            WANDminiComm.startStream(cp2130Handle)
            time.sleep(0.1)
            
        while self._running:
            data = WANDminiComm.cp2130_libusb_read(cp2130Handle)
            if data:
                if data[1] == 198:
                    sampleQueue.put(data)
        
        WANDminiComm.stopStream(cp2130Handle)
        time.sleep(0.1)
    
    def setWideIn(self, mode):
        success = False
        if not self._running:
            val, readSuccess = WANDminiComm.readReg(cp2130Handle,0,0x0C)
            if not readSuccess:
                print('Failed to read wide input register!')
            else:
                value = val
                if mode:
                    # trying to enable wide input
                    if not (value % 2):
                        # wide input is disabled
                        value = value + 1
                        if (WANDminiComm.writeReg(cp2130Handle,0,0x0C,value)):
                            print('Wide input mode enabled!')
                            success = True
                        else:
                            print('Unable to write wide input register!')
                    else:
                        print('Wide input already enabled!')
                        success = True
                else:
                    # trying to disable wide input
                    if (value % 2):
                        # wide input is enabled
                        value = value - 1
                        if (WANDminiComm.writeReg(cp2130Handle,0,0x0C,value)):
                            print('Wide input mode disabled!')
                            success = True
                        else:
                            print('Unable to write wide input register!')
                    else:
                        print('Wide input already disabled!')
                        success = True
        else:
            print('Cannot set wide input while streaming!')
        return success

class processThread(QThread):

    plotDataReady = pyqtSignal(list)

    def __init__(self):
        QThread.__init__(self)
        self._running = False
        self.samples = 0

    def __del__(self):
        self.wait()

    def stop(self,saveDataChecked):
        self._running = False
        self.saveDataChecked = saveDataChecked

    def run(self):
        if not self._running:
            self._running = True
            self.samples = 0
            plotData = []
            self.saveData = []
            self.crcFlag = []
            self.crcSamples = 0
            print('Beginning stream')
            self.numMins = 0
        
        while self._running:
            try:
                data = sampleQueue.get(block=False)
                self.samples = self.samples + 1
                if data[0]==0x00: # no CRC
                    self.values = [(data[2*(i+1) + 1] << 8 | data[2*(i+1)]) & 0xFFFF for i in range(0,67)]
                    plotData.append(self.values)
                else: # has CRC
                    self.crcSamples += 1
                    plotData.append(self.values)
                    self.values = [(data[2*(i+1) + 1] << 8 | data[2*(i+1)]) & 0xFFFF for i in range(0,67)]
                self.saveData.append(self.values)
                self.crcFlag.append(data[0])
                if self.samples % 50 == 0:
                    self.plotDataReady.emit(plotData)
                    plotData = []
                if self.samples % 60000 == 0:
                    self.numMins += 1
                    print('    Streaming for {} mins'.format(self.numMins))
                elif self.samples % 30000 == 0:
                    print('    Streaming for {} mins and 30 sec'.format(self.numMins))
            except Empty:
                time.sleep(0.0001)

        
        if self.saveData:
            print("Received total of {} samples".format(self.samples))
            print("    with {} CRCs (error rate = {})".format(self.crcSamples, self.crcSamples/self.samples))
            if self.saveDataChecked:
                saveDir = './data/'
                outputFileName = datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + '.mat'
                matData = np.asarray(self.saveData)
                matCrc = np.asarray(self.crcFlag)
                sio.savemat(saveDir+outputFileName, dict(raw=matData,crc=matCrc))
                print("Data saved at " + "\n    " + saveDir + outputFileName)

# subclass QMainWindow to customize
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        # create main window
        self.setWindowTitle("WANDmini Simple GUI")
        # create layout
        self.layout = QGridLayout()

        # plotting area
        self.plotArea = pg.GraphicsLayoutWidget()
        self.numPlots = 4
        self.xRange = 2000
        self.plots = []
        self.plotLineRefs = []
        self.plotScrollData = []
        self.plotPlaceData = []
        self.plotXPlace = 0
        self.plotTime = list(range(-self.xRange,0))

        # channel selection boxes
        self.plotCh = []
        for i in range(0, self.numPlots):
            self.plotCh.append(QSpinBox())
            self.plotCh[i].setMinimum(0)
            self.plotCh[i].setMaximum(63)
            self.plotCh[i].setSingleStep(1)
        self.plotCh[0].setValue(0)
        self.plotCh[1].setValue(1)
        self.plotCh[2].setValue(2)
        self.plotCh[3].setValue(3)

        # scroll style selection
        self.scrollStyle = QComboBox()
        self.scrollStyle.addItem('Plot continous scroll')
        self.scrollStyle.addItem('Plot in place')

        for i in range(0, self.numPlots):
            viewBox = pg.ViewBox(enableMouse=False)
            self.plots.append(self.plotArea.addPlot(row=i,col=0,viewBox=viewBox))
            self.plotScrollData.append([0]*self.xRange)
            self.plotPlaceData.append([0]*self.xRange)
            if self.scrollStyle.currentIndex() == 0:
                self.plotLineRefs.append(self.plots[i].plot(x=self.plotTime,y=self.plotScrollData[i]))
            if self.scrollStyle.currentIndex() == 1:
                self.plotLineRefs.append(self.plots[i].plot(y=self.plotPlaceData[i]))

        # basic stream button
        self.streamButton = QPushButton('Stream from Ch:')
        self.streamButton.setCheckable(True)
        self.streamButton.clicked.connect(self.stream)

        # save checkbox
        self.saveDataCheck = QCheckBox('Save stream to file')
        self.saveDataCheck.setCheckable(True)
        self.saveDataCheck.setChecked(True)

        # save checkbox
        self.wideCheck = QCheckBox('Wide input')
        self.wideCheck.setCheckable(True)
        self.wideCheck.setChecked(False)
        self.wideCheck.clicked.connect(self.wideSet)

        # stdout output
        self.stdoutText  = QTextEdit()
        self.stdoutText.moveCursor(QTextCursor.Start)
        self.stdoutText.ensureCursorVisible()
        self.stdoutText.setLineWrapMode(QTextEdit.NoWrap)

        # add widgets to layout
        self.layout.addWidget(self.plotArea,0,0,10,5)
        self.layout.addWidget(self.streamButton,11,0,1,1)
        self.layout.addWidget(self.plotCh[0],11,1,1,1)
        self.layout.addWidget(self.plotCh[1],11,2,1,1)
        self.layout.addWidget(self.plotCh[2],11,3,1,1)
        self.layout.addWidget(self.plotCh[3],11,4,1,1)
        self.layout.addWidget(self.scrollStyle,12,0,1,2)
        self.layout.addWidget(self.saveDataCheck,12,2,1,1)
        self.layout.addWidget(self.wideCheck,12,3,1,1)
        
        self.layout.addWidget(self.stdoutText,13,0,1,5)        

        self.widget = QWidget()
        self.widget.setLayout(self.layout)

        # put widget contents into main window
        self.setCentralWidget(self.widget)

        self.cp2130Thread = cp2130Thread()
        self.processThread = processThread()
        self.processThread.plotDataReady.connect(self.plotDataReady)

        # connect stdout to text box
        self.stdHandler = StdoutHandler()
        self.stdHandler.written.connect(self.onUpdateText)
        sys.stdout = self.stdHandler
    
    def __del__(self):
        sys.stdout = sys.__stdout__

    def onUpdateText(self, text):
        cursor = self.stdoutText.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.stdoutText.setTextCursor(cursor)
        self.stdoutText.ensureCursorVisible()

    def stream(self):
        # starting and stopping stream with single button
        if self.streamButton.isChecked():
            self.wideCheck.setEnabled(False)
            
            self.processThread.start()
            self.cp2130Thread.start()
        else:
            self.cp2130Thread.stop()
            self.processThread.stop(self.saveDataCheck.isChecked())

            self.wideCheck.setEnabled(True)

    def wideSet(self):
        if not self.cp2130Thread.setWideIn(self.wideCheck.isChecked()):
            self.wideCheck.toggle()

    # called everytime process thread emits new data
    @pyqtSlot(list)
    def plotDataReady(self,data):
        self.plotTime = self.plotTime[len(data):]
        self.plotTime.extend(list(range(self.plotTime[-1]+1,self.plotTime[-1]+1+len(data))))
        if self.scrollStyle.currentIndex() == 0:
            self.plotXPlace = (self.plotXPlace + len(data))%self.xRange
            for i in range(0, self.numPlots):
                self.plotScrollData[i] = self.plotScrollData[i][len(data):]
                self.plotScrollData[i].extend([sample[self.plotCh[i].value()] for sample in data])
                self.plotLineRefs[i].setData(x=self.plotTime,y=self.plotScrollData[i])
        elif self.scrollStyle.currentIndex() == 1:
            for i in range(0,len(data)):
                for ch in range(0,self.numPlots):
                    self.plotPlaceData[ch][self.plotXPlace] = data[i][self.plotCh[ch].value()]
                self.plotXPlace += 1
                if self.plotXPlace == self.xRange:
                    self.plotXPlace = 0
            for ch in range(0,self.numPlots):
                self.plotLineRefs[ch].setData(y=self.plotPlaceData[ch])
        
    def closeEvent(self, event):
        self.cp2130Thread.quit()
        self.processThread.quit()

if __name__ == "__main__":
    # raw samples read from base station
    sampleQueue = Queue()

    # open connection to cp2130 base station
    cp2130Handle, kernelAttached, deviceList, context = WANDminiComm.open_cp2130()

    # test for connection with board
    if not(WANDminiComm.writeReg(cp2130Handle,0,0x0F,0xBEEF)):
        # quit program if no connection found
        print('Could not find WANDmini, exiting!')
    else:
        print('Successfully connected to WANDmini!')
        # main application instance
        app = QApplication([])

        # force the style to be the same on all OSs:
        app.setStyle("Fusion")

        # Now use a palette to switch to dark colors:
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        app.setPalette(palette)

        # set up things here before starting event loop
        window = MainWindow()
        window.resize(800, 800)
        window.show()

        # start event loop
        ret = app.exec_()

        # reach here after closing window
        window.cp2130Thread.quit()
        window.processThread.quit()
        del window
        sys.exit(ret)