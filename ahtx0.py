from microbit import i2c, sleep
from micropython import const

class AHT10:
    __DEFAULTADDRESS = const(0x38) # Default I2C address
    __CMD_INITIALIZE = const(b'\xE1\x08\x00') # Initialization command
    __CMD_TRIGGER = const(b'\xAC\x33\x00')  # Trigger reading command
    __CMD_SOFTRESET = const(b'\xBA')  # Soft reset command
    __STATUS_BUSY = const(0x80)  # Status bit for busy
    __STATUS_CALIBRATED = const(0x08)  # Status bit for calibrated

    def __init__(self, address = __DEFAULTADDRESS):
        sleep(20)
        self.__address = address
        self.__buf = bytearray(6)

        self.reset()
        if not self.__initialize():
            raise RuntimeError("Could not initialize")
    
    def reset(self):
        """Perform a soft-reset of the AHT"""
        try:
            i2c.write(self.__address, self.__CMD_SOFTRESET)
        except OSError:
            raise RuntimeError("Could not send CMD_SOFTRESET")
        sleep(20)
        
    def __initialize(self):
        """Ask the sensor to self-initialize. Returns True on success, False otherwise"""
        try:
            i2c.write(self.__address, self.__CMD_INITIALIZE)
        except OSError:
            raise RuntimeError("Could not send CMD_INITIALIZE")
        self.__wait_for_idle()
        if not self.status() & self.__STATUS_CALIBRATED:
            return False
        return True
        
    def status(self):
        """The status byte initially returned from the sensor, see datasheet for details"""
        self.__read_to_buffer()
        return self.__buf[0]
    
    def relative_humidity(self):
        """The measured relative humidity in percent."""
        self.__perform_measurement()
        humidity = (self.__buf[1] << 12) | (self.__buf[2] << 4) | (self.__buf[3] >> 4)
        humidity = (humidity * 100) / 0x100000
        return humidity
    
    def temperature(self):
        """The measured temperature in degrees Celcius."""
        self.__perform_measurement()
        temp = ((self.__buf[3] & 0xF) << 16) | (self.__buf[4] << 8) | self.__buf[5]
        temp = ((temp * 200.0) / 0x100000) - 50
        return temp
    
    def __read_to_buffer(self):
        """Read sensor data to buffer"""
        try :
            self.__buf = i2c.read(self.__address, 6) # number of bytes to be read
        except OSError:
            raise RuntimeError("Could not read from sensor")
    
    def __trigger_measurement(self):
        """Internal function for triggering the AHT to read temp/humidity"""
        try:
            i2c.write(self.__address, self.__CMD_TRIGGER)
        except OSError:
            raise RuntimeError("Could not send CMD_TRIGGER")
    
    def __wait_for_idle(self):
        """Wait until sensor can receive a new command"""
        while self.status() & self.__STATUS_BUSY:
            sleep(5)

    def __perform_measurement(self):
        """Trigger measurement and write result to buffer"""
        self.__trigger_measurement()
        self.__wait_for_idle()
        self.__read_to_buffer()
