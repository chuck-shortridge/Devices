import serial
import serial.tools.list_ports
from time import time, sleep
import platform

if platform.system().lower() != 'windows':
    import fcntl
else:
    from fakefcntl import fcntl


def find_first_board():
    try:
        boards = find_boards()
        b = next(boards)
    except:
        b = None
    return b


def find_boards():
    for p in serial.tools.list_ports.comports():
        try:
            if p.device == '/dev/ttyAMA0':
                continue
            with open(p.device, 'r') as a:
                if platform.system().lower() != 'windows':
                    fcntl.flock(a.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except Exception as e:
            print('No Board: ' + str(e))
            sleep(.1)
            continue
        with serial.Serial(p.device, 57600, timeout=.4, write_timeout=.4) as ser:
            try:
                ser.reset_input_buffer()
                ser.reset_output_buffer()
                ser.write(b'?ID\r')
                resp = ser.read_until(b'\r')
                if resp.decode("utf-8")[:2] == 'ID':
                    if 'CS-5090' in resp.decode("utf-8"):
                        #print('CS-5090: ' + p.device)
                        yield p.device
                    ser.reset_input_buffer()
                    ser.reset_output_buffer()
                    ser.write(b'?STAT\r')
                    resp = ser.read_until(b'\r')
                    if resp.decode("utf-8")[:4] == 'STAT':
                        #print('Cordis: ' + p.device)
                        ser.close()
                        yield p.device
            except Exception as e:
                print('No Board: ' + str(e))
                continue
            finally:
                ser.close()


class CordisDevice():
    def __init__(self, device):
        self.SerialPort = None
        self.Serial_Number = '~No Board Found~'
        self.Model_Number = '~No Board Found~'
        self.Device_Type = 'Control'
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

    def get_firmware(self):
        r = ''
        if 'CS-5090' in self.Model_Number:
            r = ''
        else:
            r = self.get_resp('FW')
        self.Firmware = r
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

    def get_valveliftoff(self):
        r = ''
        r = self.get_resp('VLO')
        self.VLO = r
        return r

    def get_pidp(self):
        r = ''
        r = self.get_resp('PIDP')
        self.PID_P = r
        return r

    def get_pidi(self):
        r = ''
        r = self.get_resp('PIDI')
        self.PID_I = r
        return r

    def get_pidd(self):
        r = ''
        r = self.get_resp('PIDD')
        self.PID_D = r
        return r

    def get_commandzero(self):
        r = ''
        r = self.get_resp('CZERO')
        self.Command_Zero = r
        return r

    def get_commandfullscale(self):
        r = ''
        r = self.get_resp('CFS')
        self.Command_Fullscale = r
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

    def get_commandtype(self):
        r = ''
        r = self.get_resp('CT')
        self.Command_Type = r
        return r

    def get_ibias(self):
        r = ''
        r = self.get_resp(
            'IBIAS' if 'CS-5090' not in self.Model_Number else 'BIAS')
        self.IBIAS = r
        return r

    def get_ebias(self):
        r = ''
        r = self.get_resp('EBIAS')
        self.EBIAS = r
        return r

    def get_cutoff(self):
        r = ''
        r = self.get_resp(
            'CO' if 'CS-5090' not in self.Model_Number else 'CUTOFF')
        self.Cutoff = r
        return r

    def get_vlo(self):
        r = ''
        r = self.get_resp('VLO')
        self.VLO = r
        return r

    def get_flow(self):
        r = ''
        r = self.get_resp('FLOW')
        self.Flow = r
        return r

    def get_status(self):
        if 'CS-5090' in self.Model_Number:
            c = ''
            s = ''
            e = ''
        else:
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

    def get_command_type(self):
        r = ''
        r = '0' if 'CS-5090' in self.Model_Number else self.get_resp('CT')
        self.Command_Type = r
        return r

    def set_commandtype(self, value):
        return self.set_command_type(value)

    def set_command_type(self, value):
        cmd = 'CT'
        retval = ''
        retval = self.set_value(cmd, value)
        self.Command_Type = retval
        if retval == cmd:
            return 0
        else:
            return 1

    def get_current_command(self):
        r = ''
        r = '0' if 'CS-5090' in self.Model_Number else self.get_resp('CC')
        # r = self.get_resp('CC')
        self.Current_Command = r
        return r

    def set_current_command(self, value):
        cmd = 'CC'
        retval = ''
        retval = self.set_value(cmd, value)
        self.Current_Command = retval
        if retval == cmd:
            return 0
        else:
            return 1

    def set_pidp(self, value):
        cmd = 'PIDP'
        retval = ''
        retval = self.set_value(cmd, value)
        self.PID_P = retval
        if retval == cmd:
            return 0
        else:
            return 1

    def set_pidi(self, value):
        cmd = 'PIDI'
        retval = ''
        retval = self.set_value(cmd, value)
        self.PID_I = retval
        if retval == cmd:
            return 0
        else:
            return 1

    def set_pidd(self, value):
        cmd = 'PIDD'
        retval = ''
        retval = self.set_value(cmd, value)
        self.PID_D = retval
        if retval == cmd:
            return 0
        else:
            return 1

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

    def set_valveliftoff(self, value):
        cmd = 'VLO'
        retval = ''
        retval = self.set_value(cmd, value)
        self.VLO = retval
        if retval == cmd:
            return 0
        else:
            return 1

    def set_commandzero(self, value):
        cmd = 'CZERO'
        retval = ''
        retval = self.set_value(cmd, value)
        self.Command_Zero = retval
        if retval == cmd:
            return 0
        else:
            return 1

    def set_commandfullscale(self, value):
        cmd = 'CFS'
        retval = ''
        retval = self.set_value(cmd, value)
        self.Command_Fullscale = retval
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

    def set_sensorfullscale(self, value):
        cmd = 'SFS'
        retval = ''
        retval = self.set_value(cmd, value)
        self.Sensor_Fullscale = retval
        if retval == cmd:
            return 0
        else:
            return 1

    def set_ebias(self, value):
        cmd = 'EBIAS'
        retval = ''
        retval = self.set_value(cmd, value)
        self.EBIAS = retval
        if retval == cmd:
            return 0
        else:
            return 1

    def set_ibias(self, value):
        cmd = 'IBIAS' if 'CS-5090' not in self.Model_Number else 'BIAS'
        retval = ''
        retval = self.set_value(cmd, value)
        self.IBIAS = retval
        if retval == cmd:
            return 0
        else:
            return 1

    def set_flow(self, value):
        cmd = 'FLOW'
        retval = ''
        retval = self.set_value(cmd, value)
        self.Flow = retval
        if retval == cmd:
            return 0
        else:
            return 1

    def set_cutoff(self, value):
        cmd = 'CUTOFF' if 'CS-5090' in self.Model_Number else 'CO'
        retval = ''
        retval = self.set_value(cmd, value)
        self.Cutoff = retval
        if retval == cmd:
            return 0
        else:
            return 1
    '''
    def leaktest(self, testtime):
        while self.Waiting:
            pass
        self.Waiting = True
        try:
            self.SerialPort.write(b'\r')
            self.SerialPort.read(65535)
            self.SerialPort.write(b'LEAKTEST ' + str(testtime).encode() + b'\r')
            resp = b''
            while not 'of FS' in resp.decode('utf-8'):
                resp = self.SerialPort.read_until('\r')

            self.Waiting = False
            return resp.decode('utf-8')
        except:
            self.Waiting = False
            return 'error'
    '''

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

    def enable_both(self):
        self.disable_valves(0)
        self.InletEnabled = True
        self.ExhaustEnabled = True

    def disable_both(self):
        self.disable_valves(5)
        self.InletEnabled = False
        self.ExhaustEnabled = False

    def enable_inlet(self):
        self.disable_valves(1)
        self.InletEnabled = True

    def disable_inlet(self):
        self.disable_valves(2)
        self.InletEnabled = False

    def enable_exhaust(self):
        self.disable_valves(3)
        self.ExhaustEnabled = True

    def disable_exhaust(self):
        self.disable_valves(4)
        self.ExhaustEnabled = False

    def disable_valves(self, value):
        cmd = 'DVALVE'
        retval = ''
        retval = self.set_value(cmd, value)
        if retval == cmd:
            return 0
        else:
            return 1

    def leaktest(self, max_allowable=-0.4):
        instat = self.InletEnabled
        exstat = self.ExhaustEnabled
        self.disable_both()
        startmon = float(self.get_status()[1])
        starttime = time()
        mon = startmon
        while mon - startmon >= max_allowable:
            mon = float(self.get_status()[1])
        if instat:
            self.enable_inlet()
        if exstat:
            self.enable_exhaust()

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
    Cordis = CordisDevice(find_first_board())
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
