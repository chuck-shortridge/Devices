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
        self.Serial_Number = '~No Board Found~'
        self.Model_Number = '~No Board Found~'
        self.Device_Type = 'Control'
        self.Sensor_Zero = ''
        self.Sensor_Fullscale = ''
        self.Monitor_Zero = ''
        self.Monitor_Fullscale = ''
        self.Waiting = False

        if device is not None:
            self.SerialPort = serial.Serial(device, 57600, timeout=.4)
            if platform.system().lower() != 'windows':
                fcntl.flock(self.SerialPort.fileno(),
                            fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.get_serialnumber()
            if not 'error' in self.Serial_Number:
                self.get_all_values()
                self.Serial_Number = '~No Board Found~'
        else:
            self.SerialPort = None
            self.Serial_Number = '~No Board Found~'
            self.Model_Number = '~No Board Found~'

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

    def get_monitor(self):
        r = ''
        if 'CS-5090' in self.Model_Number:
            r = ''
        else:
            r = self.get_resp('MON')
        self.Monitor = r
        return r

    def get_monitorzero(self):
        r = ''
        r = self.get_resp('MZERO')
        self.Monitor_Zero = r
        return r

    def get_monitorfullscale(self):
        r = ''
        r = self.get_resp('MFS')
        self.Monitor_Fullscale = r
        return r

    def get_sensorzero(self):
        r = ''
        r = self.get_resp('SZERO')
        self.Sensor_Zero = r
        return r

    def get_sensorfullscale(self):
        r = ''
        r = self.get_resp('SFS')
        self.Sensor_Fullscale = r
        return r

    def get_status(self):
        r = ':  :  :'
        r = self.get_resp('STAT')
        c = 'Err'
        s = 'Err'
        e = 'Err'
        if r.startswith(' C:'):
            try:
                r.lstrip()
                c = r.split('  ')[0].split(':')[1]
                s = r.split('  ')[1].split(':')[1]
                e = r.split('  ')[2].split(':')[1]
            except Exception as ex:
                pass
        self.Command = str(c)
        self.Monitor = str(s)
        return c, s, e

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

    def set_monitorzero(self, value):
        cmd = 'MZERO'
        retval = ''
        retval = self.set_value(cmd, value)
        self.Monitor_Zero = retval
        if retval == cmd:
            return 0
        else:
            return 1

    def set_monitorfullscale(self, value):
        cmd = 'MFS'
        retval = ''
        retval = self.set_value(cmd, value)
        self.Monitor_Fullscale = retval
        if retval == cmd:
            return 0
        else:
            return 1

    def set_sensorzero(self, value):
        cmd = 'SZERO'
        retval = ''
        retval = self.set_value(cmd, value)
        self.Sensor_Zero = retval
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

    def auto_calibrate(self):
        try:
            # with serial.Serial(self.SerialPort, 57600, timeout=.5, write_timeout=.5) as ser:
            while self.Waiting:
                pass
            self.Waiting = True
            self.SerialPort.write(b'AUTOC\r')
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
            self.get_commandzero()
            self.get_commandfullscale()
            self.get_monitorzero()
            self.get_monitorfullscale()
            self.get_sensorzero()
            self.get_sensorfullscale()
            self.get_pidp()
            self.get_pidi()
            self.get_cutoff()
            self.get_ibias()
            self.get_monitor()
            self.get_current_command()
            if 'CS-5090' not in self.Model_Number:
                self.get_command_type()
                self.get_current_command()
                self.get_vlo()
                self.get_ebias()
                self.get_flow()
                self.get_status()
                self.get_pidd()
                self.get_firmware()
        else:
            self.Serial_Number = '~No Board Found~'

    def empty_values(self):
        self.Serial_Number = '~No Board Found~'
        self.Model_Number = '~No Board Found~'
        self.Command_Zero = ''
        self.Command_Fullscale = ''
        self.Sensor_Zero = ''
        self.Sensor_Fullscale = ''
        self.Monitor_Zero = ''
        self.Monitor_Fullscale = ''
        self.PID_P = ''
        self.PID_I = ''
        self.PID_D = ''
        self.Command_Type = ''
        self.Current_Command = ''
        self.VLO = ''
        self.IBIAS = ''
        self.EBIAS = ''
        self.Flow = ''
        self.Cutoff = ''
        self.Monitor = ''
        self.Command = ''
        self.Firmware = ''
        self.InletEnabled = True
        self.ExhaustEnabled = True

    def update_values(self):
        if 'CS-5090' not in self.Model_Number:
            self.get_status()


if __name__ == '__main__':
    import time
    Cordis = ExternalSensor()
    print('ID: ' + Cordis.ID)
    print('SN: ' + Cordis.SerialNumber)
    print('PIDP: ' + Cordis.get_pidp())
    print('PIDI: ' + Cordis.get_pidi())
    print('PIDD: ' + Cordis.get_pidd())
    print('CZERO: ' + Cordis.get_commandzero())
    print('CFS: ' + Cordis.get_commandfullscale())
    print('SZERO: ' + Cordis.get_sensorzero())
    print('SFS: ' + Cordis.get_sensorfullscale())
    print('CT: ' + Cordis.get_commandtype())
    print('ADC: ' + Cordis.get_status())
    while 1:
        print(Cordis.get_status())
        sleep(1)
