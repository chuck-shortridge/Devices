import serial
import serial.tools.list_ports
from time import time, sleep
import platform

if platform.system().lower() != 'windows':
    import fcntl
else:
    from fakefcntl import fcntl


class ExternalSensor():
    def __init__(self, device):
        self.SerialPort = None
        self.Serial_Number = ''
        self.Model_Number = ''
        self.Device_Type = 'Control'
        self.Output = ''
        self.Sensor_Zero = ''
        self.Sensor_Fullscale = ''
        self.Out_Zero = ''
        self.Out_Fullscale = ''
        self.Waiting = False

        if device is not None:
            self.SerialPort = serial.Serial(device, 57600, timeout=.4)
            if platform.system().lower() != 'windows':
                fcntl.flock(self.SerialPort.fileno(),
                            fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.get_serialnumber()
            if not 'error' in self.Serial_Number:
                self.get_all_values()
                self.Serial_Number = ''
        else:
            self.SerialPort = None
            self.Serial_Number = ''
            self.Model_Number = ''

    def reset_serial(self):
        while self.Waiting:
            pass
        self.Waiting = True
        if self.SerialPort:
            self.SerialPort.reset_input_buffer()
            self.SerialPort.reset_output_buffer()
        self.Waiting = False

    def get_resp(self, cmd):
        try:
            while self.Waiting:
                pass
            self.reset_serial()
            self.Waiting = True
            tmpcmd = b'?' + cmd.encode() + b'\r'                        # format command query

            # send command query
            self.SerialPort.write(tmpcmd)
            resp = self.SerialPort.read_until(b'\r')
            self.Waiting = False
            resp = resp.decode('utf-8')
            if resp == '' or resp[-1] != '\r':
                raise Exception('Unexpected Return')
            if 'CUTOFF' in cmd and 'CS-5090' in self.Model_Number:
                return resp[4:-1]
            else:
                return resp[(len(cmd)+2):-1]
        except Exception as ex:
            # self.SerialPort = None
            self.Waiting = False
            # print('error: ' + type(ex).__name__)
            return 'error: ' + type(ex).__name__

    def set_value(self, cmd, value):
        try:
            while self.Waiting:
                pass
            self.Waiting = True
            tmpcmd = b'?' + cmd.encode() + b'\r'                        # format command query
            #  with serial.Serial(self.SerialPort, 57600, timeout=.4) as ser:
            tmpcmd = cmd.encode() + b': ' + str(value).encode() + \
                b'\r'  # format command query
            self.SerialPort.write(b'\r')
            self.SerialPort.read(65535)
            # send command
            self.SerialPort.write(tmpcmd)
            resp = self.SerialPort.read_until(b'\r')
            self.Waiting = False
            return resp.decode('utf-8')[(len(cmd)+2):-1]
        except Exception as ex:
            # self.SerialPort = None
            self.Waiting = False
            return 'error'

    def get_id(self):
        r = ''
        r = self.get_resp('ID')
        self.Model_Number = r
        return r

    def get_serialnumber(self):
        r = ''
        r = self.get_resp('SN')
        self.Serial_Number = r
        return r

    def get_outzero(self):
        r = ''
        r = self.get_resp('OUT_LOW')
        self.Monitor_Zero = r
        return r

    def get_outfullscale(self):
        r = ''
        r = self.get_resp('OUT_HIGH')
        self.Monitor_Fullscale = r
        return r

    def get_sensorzero(self):
        r = ''
        r = self.get_resp('SENSOR_LOW')
        self.Sensor_Zero = r
        return r

    def get_sensorfullscale(self):
        r = ''
        r = self.get_resp('SENSOR_HIGH')
        self.Sensor_Fullscale = r
        return r

    def get_status(self):
        r = ':  :  :'
        r = self.get_resp('STAT')
        s = 'Err'
        sl = 'Err'
        sh = 'Err'
        ol = 'Err'
        oh = 'Err'
        if r.startswith(': ADC::'):
            try:
                r.lstrip()
                s = r.split(' | ')[0].split('::')[1].strip()
                sl = r.split(' | ')[1].split('::')[1].strip()
                sh = r.split(' | ')[2].split('::')[1].strip()
                ol = r.split(' | ')[3].split('::')[1].strip()
                oh = r.split(' | ')[4].split('::')[1].strip()
            except Exception as ex:
                pass
            self.Output = str(s)
            self.Sensor_Zero = str(sl)
            self.Sensor_Fullscale = str(sh)
            self.Out_Zero = str(ol)
            self.Out_Fullscale = str(oh)
        return s, sl, sh, ol, oh

    def set_serialnumber(self, value):
        cmd = '53455249414C'
        retval = ''
        retval = self.set_value(cmd, value)
        self.Serial_Number = retval
        if retval == cmd:
            return 0
        else:
            return 1

    def set_id(self, value):
        cmd = '4D4F44454C'
        retval = ''
        retval = self.set_value(cmd, value)
        self.Model_Number = retval
        if retval == cmd:
            return 0
        else:
            return 1

    def set_outzero(self, value):
        cmd = 'OUT_LOW'
        retval = ''
        retval = self.set_value(cmd, value)
        self.Monitor_Zero = retval
        if retval == cmd:
            return 0
        else:
            return 1

    def set_outfullscale(self, value):
        cmd = 'OUT_HIGH'
        retval = ''
        retval = self.set_value(cmd, value)
        self.Monitor_Fullscale = retval
        if retval == cmd:
            return 0
        else:
            return 1

    def set_sensorzero(self, value):
        cmd = 'SENSOR_LOW'
        retval = ''
        retval = self.set_value(cmd, value)
        self.Sensor_Zero = retval
        if retval == cmd:
            return 0
        else:
            return 1

    def set_sensorfullscale(self, value):
        cmd = 'SENSOR_HIGH'
        retval = ''
        retval = self.set_value(cmd, value)
        self.Sensor_Fullscale = retval
        if retval == cmd:
            return 0
        else:
            return 1

    def save(self):
        try:
            # with serial.Serial(self.SerialPort, 57600, timeout=.5, write_timeout=.5) as ser:
            while self.Waiting:
                pass
            self.Waiting = True
            self.SerialPort.write(b'SAVE\r')
            resp = self.SerialPort.read_until(b'\r')
            self.Waiting = False
            return resp.decode('utf-8')
        except:
            self.Waiting = False
            return 'error'

    def is_connected(self):
        # r = self.get_resp('ID')
        if self.SerialPort:
            return True
        else:
            return False

    def get_all_values(self):
        self.empty_values()
        self.get_serialnumber()
        if not 'error' in self.Serial_Number:
            self.get_id()
            self.get_outzero()
            self.get_outfullscale()
            self.get_sensorzero()
            self.get_sensorfullscale()
        else:
            self.Serial_Number = ''

    def empty_values(self):
        self.Serial_Number = ''
        self.Model_Number = ''
        self.Output = ''
        self.Sensor_Zero = ''
        self.Sensor_Fullscale = ''
        self.Out_Zero = ''
        self.Out_Fullscale = ''

    def update_values(self):
        self.get_status()


if __name__ == '__main__':
    import time
    Sensor = ExternalSensor()
    print('ID: ' + Sensor.ID)
    print('SN: ' + Sensor.SerialNumber)
    print('CZERO: ' + Sensor.get_outzero())
    print('CFS: ' + Sensor.get_outfullscale())
    print('SZERO: ' + Sensor.get_sensorzero())
    print('SFS: ' + Sensor.get_sensorfullscale())
    print('CT: ' + Sensor.get_commandtype())
    print('ADC: ' + Sensor.get_status())
    while 1:
        print(Sensor.get_status())
        sleep(1)
