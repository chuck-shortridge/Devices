import serial
import serial.tools.list_ports
from time import sleep
import platform

if platform.system().lower() != 'windows':
    import fcntl
else:
    from fakefcntl import fcntl


class Fluke2700:
    def __init__(self, port):
        self.DevicePort = ''
        self.SerialNumber = '-'
        self.Device_Type = 'Measurement'
        self.Pressure = ''
        self.Value = ''
        self.Unit = ''
        self.SerialPort = None
        self.Waiting = False
        resp = b''
        try:
            with serial.Serial(port, 9600, timeout=.3) as ser:
                ser.write(b'\r*idn?\r')
                resp = ser.read_until(b'\r')
        except Exception as ex:
            self.SerialPort = None
        if resp.decode('utf-8')[:11] == 'FLUKE,2700G':  # check for fluke response
            self.DevicePort = port
            # Update class variables if its a fluke
            try:
                self.SerialNumber = resp.decode('utf-8').split(',')[2]
            except:
                self.SerialNumber = '----------'
            self.SerialPort = serial.Serial(self.DevicePort, 9600, timeout=.3)
            fcntl.flock(self.SerialPort.fileno(),
                        fcntl.LOCK_EX | fcntl.LOCK_NB)
            # print('Fluke2700G: ' + str(p.device))

    def reset_serial(self):
        while self.Waiting:
            pass
        self.Waiting = True
        if self.SerialPort:
            self.SerialPort.reset_input_buffer()
            self.SerialPort.reset_output_buffer()
            pass
        self.Waiting = False

    def read_command(self, cmd):
        while self.Waiting:
            pass
        self.Waiting = True
        try:
            if self.SerialPort:
                send_bytes = b'\r' + cmd + b'\r'
                self.SerialPort.write(send_bytes)
                resp = self.SerialPort.read_until(b'\r')
                resp = resp.decode('utf-8')
                if resp == '' or resp[-1] != '\r':
                    raise Exception('Unexpected Return')
                self.Waiting = False
                return resp
            else:
                self.Waiting = False
                return "Err,Err"
        except:
            # if self.SerialPort:
            #     self.SerialPort.close()
            # self.SerialPort = None
            self.Waiting = False
            return 'Err,Err'

    def write_command(self, cmd):
        while self.Waiting:
            pass
        self.Waiting = True
        try:
            if self.SerialPort:
                self.SerialPort.write(b'\r' + cmd + b'\r')
            self.Waiting = False
        except:
            # if self.SerialPort:
            #     self.SerialPort.close()
            # self.SerialPort = None
            self.Waiting = False
            return 'Err,Err'

    def find_device(self):
        while self.Waiting:
            pass
        self.Waiting = True
        for p in serial.tools.list_ports.comports():
            try:
                if p.device == '/dev/ttyAMA0':
                    continue
                with open(p.device, 'r') as a:
                    fcntl.flock(a.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    a = 1234  # Not sure what is happening here but with only an flock it freezes
            except:
                continue
            try:
                with serial.Serial(p.device, 9600, timeout=.2) as ser:
                    ser.write(b'\r*idn?\r')
                    resp = ser.read_until(b'\r')
            except:                     # to broad of an exception ... but if it fails we should just move on
                self.SerialPort = None
                continue
            if resp.decode('utf-8')[:11] == 'FLUKE,2700G':  # check for fluke response
                self.DevicePort = p.device
                # Update class variables if its a fluke
                self.SerialNumber = resp.decode('utf-8').split(',')[2]
                self.SerialPort = serial.Serial(
                    self.DevicePort, 9600, timeout=.2)
                fcntl.flock(self.SerialPort.fileno(),
                            fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.Waiting = False
                return True
        self.Waiting = False
        return False

    def read_pressure(self):
        r = self.read_command(b'val?')
        if r != 'Err,Err' and r != '' and ',' in r:
            try:
                self.Pressure = str(float(r.split(',')[0]))
                self.Value = self.Pressure                  # for ControlBox Compatibility
            except:
                return 'Err'
        else:
            return 'Err'
        return self.Pressure

    def read_unit(self):
        r = self.read_command(b'val?')
        self.Unit = 'Err'
        if r != 'Err,Err' and r != '' and ',' in r:
            try:
                self.Unit = r.split(',')[1]
            except:
                return 'Err'
        else:
            return 'Err'
        return self.Unit

    def read_pressure(self):
        r = self.read_command(b'val?')
        self.Pressure = 'Err'
        self.Value = self.Pressure                  # for ControlBox Compatibility
        if r != 'Err,Err' and r != '' and ',' in r:
            try:
                self.Pressure = str(float(r.split(',')[0]))
                self.Value = self.Pressure                  # for ControlBox Compatibility
            except:
                return 'Err'
        else:
            return 'Err'
        return self.Pressure

    def update_values(self):
        r = self.read_command(b'val?')
        self.Pressure = 'Err'
        self.Value = self.Pressure                  # for ControlBox Compatibility
        self.Unit = 'Err'
        if r != 'Err,Err' and r != '' and ',' in r:
            try:
                self.Pressure = str(float(r.split(',')[0]))
                self.Value = self.Pressure                  # for ControlBox Compatibility
                self.Unit = r.split(',')[1].strip()
            except:
                self.Pressure = 'Err'
                self.Value = self.Pressure                  # for ControlBox Compatibility
                self.Unit = 'Err'
                return 'Err'
        else:
            return 'Err'
        return self.Unit

    def is_connected(self):
        if self.SerialPort:
            return True
        else:
            return False
