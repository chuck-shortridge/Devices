import serial
import serial.tools.list_ports
import platform

if platform.system().lower() != 'windows':
    import fcntl
else:
    from fakefcntl import fcntl


class Fluke8846:
    def __init__(self, port):
        self.DevicePort = ''
        self.SerialNumber = '-'
        self.Device_Type = 'Electrical'
        self.Value = '0'
        self.Unit = 'V'
        self.SerialPort = None
        self.Waiting = False
        resp = b''
        try:
            with serial.Serial(port, 57600, timeout=1, write_timeout=1) as ser:
                ser.write(b'\r*idn?\r')
                resp = ser.read_until(terminator=b'\r')
        except:                     # to broad of an exception ... but if it fails we should just move on
            self.SerialPort = None
        if resp.decode('utf-8')[:11] == 'FLUKE,8846A':  # check for fluke response
            self.DevicePort = port
            # Update class variables if its a fluke
            self.SerialNumber = resp.decode('utf-8').split(',')[2]
            self.SerialPort = serial.Serial(
                self.DevicePort, 57600, timeout=1, write_timeout=1)
            fcntl.flock(self.SerialPort.fileno(),
                        fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.Waiting = False

    def reset_serial(self):
        while self.Waiting:
            pass
        self.Waiting = True
        if self.SerialPort:
            self.SerialPort.reset_input_buffer()
            self.SerialPort.reset_output_buffer()
        self.Waiting = False

    def read_command(self, cmd):
        while self.Waiting:
            pass
        self.Waiting = True
        try:
            if self.SerialPort:
                self.SerialPort.write(b'\r' + cmd + b'\r')
                resp = self.SerialPort.read_until(terminator=b'\r')
                resp = resp.decode('utf-8')
                if resp == '' or resp[-1] != '\r':
                    raise Exception('Unexpected Return')
                self.Waiting = False
                return resp
            else:
                self.Waiting = False
                return "Err"
        except:
            if self.SerialPort:
                self.SerialPort.close()
            self.SerialPort = None
            self.Waiting = False
            return 'Err'

    def write_command(self, cmd):
        while self.Waiting:
            pass
        self.Waiting = True
        try:
            if self.SerialPort:
                self.SerialPort.write(b'\r' + cmd + b'\r')
            self.Waiting = False
        except:
            if self.SerialPort:
                self.SerialPort.close()
            self.SerialPort = None
            self.Waiting = False
            return 'Err'

    def find_device(self):
        while self.Waiting:
            pass
        self.Waiting = True
        for p in serial.tools.list_ports.comports():
            if p.device == '/dev/ttyAMA0':
                continue
            try:
                with open(p.device, 'r') as a:
                    fcntl.flock(a.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except:
                continue
            try:
                with serial.Serial(p.device, 57600, timeout=1, write_timeout=1) as ser:
                    ser.write(b'\r*idn?\r')
                    resp = ser.read_until(terminator=b'\r')
            except:                     # to broad of an exception ... but if it fails we should just move on
                self.SerialPort = None
                continue
            if resp.decode('utf-8')[:11] == 'FLUKE,8846A':  # check for fluke response
                self.DevicePort = p
                # Update class variables if its a fluke
                try:
                    self.SerialNumber = resp.decode('utf-8').split(',')[2]
                except:
                    self.SerialNumber = '----------'
                self.SerialPort = serial.Serial(
                    self.DevicePort.device, 57600, timeout=1, write_timeout=1)
                fcntl.flock(self.SerialPort.fileno(),
                            fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.Waiting = False
                return True
        self.Waiting = False
        return False

    def read_volts_dc(self):
        # with serial.Serial(self.device_port.device, 57600, timeout=.4, write_timeout=.2) as ser:
        #     ser.write(b'\rMEAS?\r')
        #     resp = ser.read_until(terminator=b'\r')
        self.set_remote()
        r = self.read_command(b'MEAS:VOLT:DC?')
        self.set_local()
        self.Value = r
        return r

    def read_current_dc(self):
        # with serial.Serial(self.device_port.device, 57600, timeout=.4, write_timeout=.2) as ser:
        #     ser.write(b'\rMEAS?\r')
        #     resp = ser.read_until(terminator=b'\r')
        self.set_remote()
        r = self.read_command(b'MEAS:CURR:DC?')
        self.set_local()
        self.Value = str(float(r)*1000)
        return r

    def set_remote(self):
        # with serial.Serial(self.device_port.device, 57600, timeout=.2, write_timeout=.2) as ser:
        #     ser.write(b'\rSYST:REM\r')
        #     resp = ser.read_until(terminator=b'\r')
        self.write_command(b'SYST:REM')

    def update_values(self):
        r = self.read_command(b'CONF?')
        try:
            self.Unit = r.split(' ')[0][1:].strip()
            if self.Unit == 'r':
                self.Unit = 'Err'
            self.Unit = self.Unit.replace('"', '')
            self.Unit = self.Unit.replace('VOLT', 'V')
            self.Unit = self.Unit.replace('CURR', 'mA')
        except Exception as ex:
            self.Unit = ''

        r = self.read_command(b'FETCH3?')
        self.Value = r.strip()
        if 'mA' in self.Unit:
            try:
                self.Value = str(float(self.Value)*1000)
            except Exception as ex:
                self.Value = 'Err'
        return r

    def set_current(self):
        self.set_remote()
        self.write_command(b'CONF:CURR:DC')
        self.Unit = 'mA'
        self.set_local()

    def set_voltage(self):
        self.set_remote()
        self.write_command(b'CONF:VOLT:DC')
        self.Unit = 'V'
        self.set_local()

    def set_local(self):
        # with serial.Serial(self.device_port.device, 57600, timeout=.2, write_timeout=.2) as ser:
        #     ser.write(b'\rSYST:LOC\r')
        self.write_command(b'SYST:LOC')

    def is_connected(self):
        if self.SerialPort:
            return True
        else:
            return False
