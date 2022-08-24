import serial
import serial.tools.list_ports
from time import sleep
import platform

if platform.system().lower() != 'windows':
    import fcntl
else:
    from fakefcntl import fcntl


class SureFlow:
    def __init__(self):
        self.DevicePort = ''
        self.SerialNumber = '-'
        self.Device_Type = 'Measurement'
        self.Flow = ''
        self.CCM = ''
        self.SCCM = ''
        self.Temp = ''
        self.Pressure = ''
        self.SerialPort = None
        self.Waiting = False

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
                return 'Err'
        except Exception as e:
            self.Waiting = False
            self.SerialPort = None
            return 'Err'

    def write_command(self, cmd):
        while self.Waiting:
            pass
        try:
            self.Waiting = True
            if self.SerialPort:
                self.SerialPort.write(b'\r' + cmd + b'\r')
            self.Waiting = False
        except Exception as e:
            self.Waiting = False
            self.SerialPort = None
            return 'Err'

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
                with serial.Serial(p.device, 19200, timeout=.2) as ser:
                    ser.write(b'\r*\r')
                    resp = ser.read_until(b'\r')
            except:                     # to broad of an exception ... but if it fails we should just move on
                self.SerialPort = None
                continue
            if resp.decode('utf-8')[:2] == 'A ':  # check for fluke response
                self.DevicePort = p.device
                self.SerialPort = serial.Serial(
                    self.DevicePort, 19200, timeout=.2)
                fcntl.flock(self.SerialPort.fileno(),
                            fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.Waiting = False
                self.read_serial()
                print('SureFlow: ' + str(p.device))
                return True
        self.Waiting = False
        return False

    def read_flow(self):
        r = self.read_command(b'A')
        if r != 'Err' and r != '':
            try:
                self.SCCM = str(float(r.split(' ')[4]))
                self.CCM = str(float(r.split(' ')[3]))
                self.Temp = str(float(r.split(' ')[2]))
                self.Pressure = str(float(r.split(' ')[1]))
            except:
                return 'Err'
        else:
            return 'Err'
        return self.SCCM

    def read_serial(self):
        r = self.read_command(b'A r76')
        if r != 'Err' and r != '':
            try:
                self.SerialNumber = str(int(r.split('=')[1]))
            except:
                return 'Err'
        else:
            return 'Err'
        return self.Pressure

    def is_connected(self):
        resp = self.read_flow()
        if resp == 'Err':
            return False
        else:
            return True

    def update_values(self):
        self.read_flow()
