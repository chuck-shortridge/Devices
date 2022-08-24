import serial
import serial.tools.list_ports
import platform

if platform.system().lower() != 'windows':
    import fcntl
else:
    from fakefcntl import fcntl


class Pace1000:
    def __init__(self, port):
        resp = b''
        self.Waiting = False
        self.DevicePort = ''
        self.SerialNumber = '-'
        self.Device_Type = 'Measurement'
        self.Unit = ''
        self.Pressure = ''
        self.Value = ''
        self.SerialPort = None
        try:
            with serial.Serial(port, 57600, timeout=4, write_timeout=4) as ser:
                ser.write(b'\r\n*idn?\r\n')
                resp = ser.read_until(terminator=b'\r\n')
        except Exception as ex:
            self.SerialPort = None
        # check for fluke response
        if resp.decode('utf-8')[:22] == '*IDN GE Druck,PACE1000':
            self.DevicePort = port
            # Update class variables if its a Druck
            try:
                self.SerialNumber = resp.decode('utf-8').split(',')[2]
            except Exception as ex:
                self.SerialNumber = '----------'
            self.SerialPort = serial.Serial(
                self.DevicePort, 57600, timeout=4, write_timeout=4)
            fcntl.flock(self.SerialPort.fileno(),
                        fcntl.LOCK_EX | fcntl.LOCK_NB)
            # print('Pace1000: ' + str(p.device))
            # return True

    def read_command(self, cmd):
        if self.Waiting:
            pass
        self.Waiting = True
        try:
            if self.SerialPort:
                self.SerialPort.write(b'\r\n' + cmd + b'\r\n')
                resp = self.SerialPort.read_until(terminator=b'\r\n')
                resp = resp.decode('utf-8')
                if resp == '' or resp[-1] != '\n':
                    raise Exception('Unexpected Return')
                self.Waiting = False
                return resp
            else:
                self.Waiting = False
                return "Err"
        except Exception as ex:
            # if self.SerialPort:
            #     self.SerialPort.close()
            # self.SerialPort = None
            self.Waiting = False
            return 'Err'

    def write_command(self, cmd):
        if self.Waiting:
            pass
        self.Waiting = True
        try:
            if self.SerialPort:
                self.SerialPort.write(b'\r\n' + cmd + b'\r\n')
            self.Waiting = False
        except Exception as ex:
            # if self.SerialPort:
            #     self.SerialPort.close()
            # self.SerialPort = None
            self.Waiting = False
            return 'Err'

    def reset_serial(self):
        while self.Waiting:
            pass
        self.Waiting = True
        if self.SerialPort:
            self.SerialPort.reset_input_buffer()
            self.SerialPort.reset_output_buffer()
        self.Waiting = False

    def find_device(self):
        for p in serial.tools.list_ports.comports():
            if p.device == '/dev/ttyAMA0':
                continue
            try:
                with open(p.device, 'r') as a:
                    fcntl.flock(a.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except Exception as ex:
                continue
            try:
                with serial.Serial(p.device, 57600, timeout=4, write_timeout=4) as ser:
                    ser.write(b'\r\n*idn?\r\n')
                    resp = ser.read_until(terminator=b'\r\n')
            except Exception as ex:
                self.SerialPort = None
                continue
            # check for fluke response
            if resp.decode('utf-8')[:22] == '*IDN GE Druck,PACE1000':
                self.DevicePort = p
                # Update class variables if its a fluke
                self.SerialNumber = resp.decode('utf-8').split(',')[2]
                self.SerialPort = serial.Serial(
                    self.DevicePort.device, 57600, timeout=4, write_timeout=4)
                fcntl.flock(self.SerialPort.fileno(),
                            fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
        return False

    def is_connected(self):
        if self.SerialPort:
            return True
        else:
            return False

    def read_pressure(self):
        # with serial.Serial(self.device_port.device, 57600, timeout=.4, write_timeout=.2) as ser:
        #     ser.write(b'\rMEAS?\r')
        #     resp = ser.read_until(terminator=b'\r')
        try:
            r = self.read_command(b':SENS:PRES?')
            r = r.split(' ')[1].strip()
        except Exception as ex:
            r = 'Err'
        self.Pressure = r
        self.Value = self.Pressure                  # for ControlBox Compatibility
        return r

    def read_unit(self):
        # with serial.Serial(self.device_port.device, 57600, timeout=.2, write_timeout=.2) as ser:
        #     ser.write(b'\rSYST:LOC\r')
        try:
            r = self.read_command(b':UNIT:PRES?')
            r = r.split(' ')[1].strip()
        except Exception as ex:
            r = 'Err'
        self.Unit = r
        return r

    def update_values(self):
        self.read_pressure()
        self.read_unit()
