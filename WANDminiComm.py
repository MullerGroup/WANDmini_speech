import libusb1
from ctypes import byref, create_string_buffer, c_int, sizeof, POINTER, \
    cast, c_uint8, c_uint16, c_ubyte, string_at, c_void_p, cdll, addressof, \
    c_char
import struct
from enum import Enum

# CP2130 Specific Stuff

def cp2130_libusb_write(handle, value):
    buf = c_ubyte * 13
    write_command_buf = buf(
        0x00, 0x00,
        0x01,
        0x00,
        0x01, 0x00, 0x00, 0x00)
    # populate command buffer with value to write
    write_command_buf[8:13] = value
    bytesWritten = c_int()
    usbTimeout = 500

    error_code = libusb1.libusb_bulk_transfer(handle, 0x02, write_command_buf, sizeof(write_command_buf), byref(bytesWritten), usbTimeout)
    if error_code:
        print('Error in bulk transfer (write command)! Error # {}'.format(error_code))
        return False
    return True

def cp2130_libusb_flush_radio_fifo(handle):
    buf = c_ubyte * 13
    write_command_buf = buf(
        0x00, 0x00,
        0x01,
        0x00,
        0x05, 0x00, 0x00, 0x00,
        0xAA, 0x00, 0x00, 0x00, 0x00)
    bytesWritten = c_int()
    usbTimeout = 500

    if libusb1.libusb_bulk_transfer(handle, 0x02, write_command_buf, sizeof(write_command_buf), byref(bytesWritten), usbTimeout):
        print('Error in bulk transfer!')
        return False
    return True

def cp2130_libusb_read(handle):
    buf = c_ubyte * 8
    read_command_buf = buf(
        0x00, 0x00,
        0x00,
        0x00,
        200, 0x00, 0x00, 0x00)
    bytesWritten = c_int()
    buf = c_ubyte * 200
    read_input_buf = buf()
    bytesRead = c_int()
    usbTimeout = 500

    # print('Begin Read')
    error_code = libusb1.libusb_bulk_transfer(handle, 0x02, read_command_buf, sizeof(read_command_buf), byref(bytesWritten), usbTimeout)
    if error_code:
        print('Error in bulk transfer command= {}'.format(error_code))
        return False
    if bytesWritten.value != sizeof(read_command_buf):
        print('Error in bulk transfer write size')
        print(bytesWritten.value)
        return False
    error_code = libusb1.libusb_bulk_transfer(handle, 0x81, read_input_buf, sizeof(read_input_buf), byref(bytesRead), usbTimeout)
    if error_code:
        print(bytesRead.value)
        print('Error in bulk transfer read = {}'.format(error_code))
        return False
    return read_input_buf

def cp2130_libusb_set_spi_word(handle):
    buf = c_ubyte * 2
    control_buf_out = buf(0x00, 0x09)
    usbTimeout = 500

    error_code = libusb1.libusb_control_transfer(handle, 0x40, 0x31, 0x0000, 0x0000, control_buf_out, sizeof(control_buf_out), usbTimeout)
    if error_code != sizeof(control_buf_out):
        print('Error in bulk transfer')
        return False
    print('Successfully set value of spi_word on chip:')
    return True

def cp2130_libusb_set_usb_config(handle):
    buf = c_ubyte * 10
    control_buf_out = buf(0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80)
    usbTimeout = 500

    error_code = libusb1.libusb_control_transfer(handle, 0x40, 0x61, 0xA5F1, 0x000A, control_buf_out, sizeof(control_buf_out), usbTimeout)
    if error_code != sizeof(control_buf_out):
        print('Error in bulk transfer')
        return False
    print('Successfully set value of spi_word on chip:')
    return True

def exit_cp2130(cp2130Handle, kernelAttached, deviceList, context):
    if cp2130Handle:
        libusb1.libusb_release_interface(cp2130Handle, 0)
    if kernelAttached:
        libusb1.libusb_attach_kernel_driver(cp2130Handle,0)
    if cp2130Handle:
        libusb1.libusb_close(cp2130Handle)
    if deviceList:
        libusb1.libusb_free_device_list(deviceList, 1)
    if context:
        libusb1.libusb_exit(context)
    exit()

def open_cp2130():
    print('Opening cp2130...')
    context = libusb1.libusb_context_p()
    deviceList = libusb1.libusb_device_p_p()
    deviceCount = 0
    check = 0

    deviceDescriptor = libusb1.libusb_device_descriptor()
    device = libusb1.libusb_device_p()
    cp2130Handle = libusb1.libusb_device_handle_p()

    kernelAttached = 0

    if libusb1.libusb_init(byref(context)) != 0:
        print('Could not initialize libusb!')
        exit_cp2130()

   
    deviceCount = libusb1.libusb_get_device_list(context, byref(deviceList))

    if deviceCount <= 0:
        print('No devices found!')
        exit_cp2130()

    
    for i in range(0, deviceCount):
        if libusb1.libusb_get_device_descriptor(deviceList[i], byref(deviceDescriptor)) == 0:
            if (deviceDescriptor.idVendor == 0x10C4) and (deviceDescriptor.idProduct == 0x87A0):
                device = deviceList[i]
                check = 1 
                break

    if device == None:
        print('CP2130 device not found!')
        exit_cp2130()
    
    if check == 0:
        print('CP2130 device not found')
        return

    if libusb1.libusb_open(device, byref(cp2130Handle)) != 0:
        print('Could not open device!')
        exit_cp2130()

    if libusb1.libusb_kernel_driver_active(cp2130Handle, 0) != 0:
        libusb1.libusb_detach_kernel_driver(cp2130Handle, 0)
        kernelAttached = 1

    if libusb1.libusb_claim_interface(cp2130Handle, 0) != 0:
        print('Could not claim interface!')
        exit_cp2130()

    if cp2130_libusb_set_usb_config(cp2130Handle) == False:
        exit_cp2130()
    if cp2130_libusb_set_spi_word(cp2130Handle) == False:
        exit_cp2130()

    print('Successfully opened CP2130!')
    return cp2130Handle, kernelAttached, deviceList, context

# NM Communcation Stuff

class Cmd(Enum):
    Reset = 0x01
    ClearErr = 0x02
    HvLoad = 0x03
    ImpStart = 0x04
    StimReset = 0x08
    StimStart = 0x09
    StimXfer = 0x0a

# CM register addresses
class Reg(Enum):
    ctrl = 0x00
    rst = 0x04
    n0d1 = 0x10
    n0d2 = 0x14
    n1d1 = 0x20
    n1d2 = 0x24
    req = 0xff
    stimExp = 0xAF

def regWr(handle, reg, value):
    cp2130_libusb_write(handle, [reg.value, *struct.pack('>I', value)])

def startStream(handle):
    regWr(handle, Reg.req, 0x0020)

def stopStream(handle):
    regWr(handle, Reg.req, 0x0010)

def writeOp(handle, nm, addr, data):
    if nm == 0:
        regWr(handle, Reg.n0d1, 1)
        regWr(handle, Reg.n0d2, addr << 16 | data)
        regWr(handle, Reg.ctrl, 0x1000)
                
    if nm == 1:
        regWr(handle, Reg.n1d1, 1)
        regWr(handle, Reg.n1d2, addr << 16 | data)
        regWr(handle, Reg.ctrl, 0x2000)

def sendCmd(handle, nm, cmd):
        # print('Send Command')
        if nm==0:
            regWr(handle, Reg.n0d2, 1<<10 | (cmd & 0x3FF))
            regWr(handle, Reg.ctrl, 0x1010)
        if nm==1:
            regWr(handle, Reg.n1d2, 1<<10 | (cmd & 0x3FF))
            regWr(handle, Reg.ctrl, 0x2020)

def readReg(handle, nm, addr):
    buf = c_ubyte*200
    d = buf()
    count = 0

    if nm == 0:
        regWr(handle, Reg.n0d1, 0)
        regWr(handle, Reg.n0d2, addr << 16 | 0)
        regWr(handle, Reg.ctrl, 0x1000)
        cp2130_libusb_flush_radio_fifo(handle)
        regWr(handle, Reg.req, 0x0100)
    else:
        regWr(handle, Reg.n1d1, 0)
        regWr(handle, Reg.n1d2, addr << 16 | 0)
        regWr(handle, Reg.ctrl, 0x2000)
        cp2130_libusb_flush_radio_fifo(handle)
        regWr(handle, Reg.req, 0x0200)

    while d[1] != 4 and count < 150:
        d = cp2130_libusb_read(handle)
        count = count + 1
    if d[1] == 4:
        add = d[2] + 256*d[3]
        val = d[4] + 256*d[5]
        if add == addr:
            # print('Register {}: {}'.format(hex(add), hex(val)))
            return val, True
        else:
            return val, False
    else:
        return 0, False

def writeReg(cp2130Handle, nm, addr, data):
    timeout = 10
    success = False
    while not success:
        timeout = timeout - 1
        if timeout == 0:
            break
        writeOp(cp2130Handle, nm, addr, data)
        readSuccess = False
        readTimeout = 10
        while not readSuccess:
            readTimeout = readTimeout - 1
            if readTimeout == 0:
                break
            val, readSuccess = readReg(cp2130Handle,0,addr)
        if readSuccess:
            success = val == data
    return success

def clearErr(cp2130Handle,nm):
    sendCmd(cp2130Handle,nm,Cmd.ClearErr.value)
