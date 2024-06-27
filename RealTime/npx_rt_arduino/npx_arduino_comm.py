import struct,time,json
import serial
import remi

class npx_arduino_comm:
    ser = None
    def connect(self,port='COM4',baudrate=9600):
        self.ser = serial.Serial(port , baudrate)
        time.sleep(2)
        print('Arduino Established')
        msg=self.ser.readline()
        return msg.decode('utf-8')
    def switch_paradigm(self):
        self.ser.write(b'1')
        time.sleep(1)
        msg=self.ser.readline()
        print(msg)
        return msg.decode('utf-8')

    def disconnect(self):
        self.ser.close()
        print('arduino disconnected')
        return 'arduino disconnected'
    
    def __init__(self):
        pass

class ArduinoGUI(remi.App):
    arduino =None
    def __init__(self, *args, **kwargs):
        super(ArduinoGUI, self).__init__(*args)
        self.arduino = npx_arduino_comm()

    def main(self):
        container = remi.gui.VBox()

        # Create status label
        self.status_label = remi.gui.Label('Ready to Connect to Arduino...')

        

        # Create switch paradigm button
        buttons_container = remi.gui.HBox()
        switch_button = remi.gui.Button('Switch Paradigm')
        switch_button.onclick.do(self.on_switch_button_click)

        connect_button = remi.gui.Button('Connect')
        connect_button.onclick.do(self.on_connect_button_click)

        disconnect_button = remi.gui.Button('Disconnect')
        disconnect_button.onclick.do(self.on_disconnect_button_click)
        
        
        buttons_container.append(connect_button)
        buttons_container.append(switch_button)
        buttons_container.append(disconnect_button)
        container.append(buttons_container)
        container.append(self.status_label)
        

        return container

    def on_switch_button_click(self, widget):
        msg=self.arduino.switch_paradigm()
        self.status_label.set_text(msg)
    def on_connect_button_click(self, widget):
        msg=self.arduino.connect()
        self.status_label.set_text(msg)
    def on_disconnect_button_click(self, widget):
        msg=self.arduino.disconnect()
        self.status_label.set_text(msg)

    def on_close(self):
        if self.arduino.ser is not None and self.arduino.ser.is_open:
            self.arduino.disconnect()
        self.close()
if __name__ == "__main__":
    remi.start( ArduinoGUI)
   