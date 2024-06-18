"""
**********************************************************
Sensapex uMP control 
wraps libump and uses minimal browser-based UI  (remi) 
logs the position to a file
**********************************************************
Vitaly Lerner 
         September 2023 
**********************************************************
Requirements: 
    numpy pandas remi
    
    library libumb.dll, libump.lib should be copied to a directory
    "sensapex". This is quite weird but I found no other solution 
**********************************************************
Glossary:
    remi: minimalistic GUI package, works as a server on local machine
          and the widgets (buttons, labels, text...) are in a browser
          which acts as a client
    widget: element of UI: button, label, text input, dropdown menu      
    Sensapex: company that manufactures the micropanipulator
    uMp, ump: micromaipulator, 4 axes: X,Y,Z,D
**********************************************************
The program operates in a "labview"-style: 
    parallel state machines (a-la LV while loops)

the state machines are:
    connection: maintains the connection with uMp
    display: updates the 
    acquire: reads the current position of the manipulator
    clock:   updates the clock UI 
    save:    saves the data to a log file

main function creates the UI elements
**********************************************************
TODO: 
    replace the logging with communication with OpenEphys
2023 10 04 
    added savemat, according to Aki's requirements
**********************************************************    
"""

from sensapex import UMP
from sensapex.sensapex import UMError
import numpy as np
import pandas as pd
from threading import Timer
from datetime import datetime

import remi.gui as gui
from remi import start, App
from scipy.io import savemat

class SensapexUI(App):
    # This class is a typical Remi program
    # 
    m=None
    connstate="Init" 
    pos=[]
    homepos=[0,0,0,0]
    
    flags={'STOP':False}
    timers={'acquire':0.1,'display':0.5,'clock':0.2,'connection':5,'save':10,'savemat':1}
    
    

    def connection_loop(self):
    # State machine: Maintains connection to the device. If disconnected, waits for the device
    # to reconnect. 
    # States: "init","waiting for device','connected'
        if (self.connstate=='Init') or (self.connstate=="WaitingForDevice"):
                          
            ump = UMP.get_ump()
            dev_ids = ump.list_devices()
            num_devices=len(dev_ids)
            #print (f"connloop {num_devices}")
            if num_devices<1:
                self.connstate="WaitingForDevice"
                Timer(self.timers['connection'],self.connection_loop).start()
                
            else:
                self.m=ump.get_device(dev_ids[0])
                self.connstate="Connected"
                self.ump=ump
                #print ("connected successfully")
                Timer(self.timers['connection'],self.connection_loop).start()
        elif (self.connstate=="Connected"):
            dev_ids = self.ump.list_devices()
            num_devices=len(dev_ids)
            if num_devices==0:
                self.connstate="WaitingForDevices"
                self.pos=[-200000]*4
            Timer(self.timers['connection'],self.connection_loop).start()
            
    def __init__(self, *args):
        # main constructor, nothing is done  here besides 
        # remi logics
        super(SensapexUI, self).__init__(*args)
        
        
        
    def jumpby(self,step:float,speed:float):
        #movemnt only in D-axis
        
        d=self.pos[3]
        newpos=[p for p in self.pos]
        newpos[3]=d+step
        self.m.stop()

        self.m.goto_pos( (newpos[0],newpos[1],newpos[2],newpos[3]),speed=speed)

        
        
    def acquire(self):
        try:
            if self.connstate=="Connected":
                self.pos=self.m.get_pos()
        except UMError:
            self.connstate="WaitingForDevice"
            self.pos=[0]*4
        if not self.flags['STOP']:
            Timer(self.timers['acquire'],self.acquire).start()
            
    def display(self):
        #print(self.pos)
        
        if self.connstate=="Connected":
            for ikey,key in enumerate(['X','Y','Z','D']):
                val=np.round(self.pos[ikey]/1000,3)
                valhome=np.round(self.homepos[ikey]/1000,3)
                val_rel=np.round(val-valhome,3)
                self.POS_DISP[key].set_text(f'{val}')
                self.RELPOS_DISP[key].set_text(f'{val_rel}')
        if not self.flags['STOP'] :        
            Timer(self.timers['display'],self.display).start()
                    
    def clock(self):
        now_t=datetime.now()
        tm=now_t.strftime("%Y.%m.%d %H:%M:%S")
        self.lblTime.set_text(tm)
        self.lblConnection.set_text(self.connstate)
        if not self.flags['STOP']:
            Timer(self.timers['clock'],self.clock).start()
            
    def savemat(self):
        #save the relative depth (D-axis) to the file that
        # StartRec program reads
        if self.MatlabCommunicate.get_value():
            fName='C:/Users/DeAngelis Lab/Documents/MATLAB/StartRec/SENSAPEX_depth.mat'
            d={'depth':int(np.round(self.pos[3]-self.homepos[3]))}
            savemat(fName,d)
        
        if not self.flags['STOP']:
            Timer(self.timers['savemat'],self.savemat).start()
        
    def save(self):
        fName_DIR=str(self.Save['Dir'].get_text())
        fName_SUB='/m'+self.Save['Subject'].get_text()
        fName_Cell='c'+self.Save['Cell'].get_text()
        fName=fName_DIR+fName_SUB+fName_Cell+'_position.txt'
        
        dtstr=self.lblTime.get_text()
        
        ln=[dtstr,self.connstate]+[f"{int(np.round(a))}" for a in self.pos]+[f"{int(np.round(a))}" for a in self.homepos]
        with open(fName,"a") as f:
            for v in ln:
                f.write(v)
                f.write(",")
            f.write("\n")
        
#        print (ln) 
#        print (fName)
        if not self.flags['STOP']:
            Timer(self.timers['save'],self.save).start()
            
    def main(self):
        lbl_style={'background':'black','color':'#A0A0A0','font-family':'Lucida Console'}
        title_style={'background':'black','color':'#C0C0C0','font-family':'Lucida Console','font-size':'16'}
        status_style={'background':'black','color':'#D0D0D0','font-family':'Lucida Console'}
        ctr_style={'background':'black'}
        inp_style={'background':'#202020','color':'#A0A0A0','font-family':'Lucida Console','vertical-align':'bottom'}
        
        left_style={'justify-content':'left','background':'black'}
        right_style={'justify-content':'right','background':'black'}
        W=600
        h=20
        
        fld_w=50
        lbl_w=10
        
        H=h*10
        
        #Title row
        Layout_TopRow = gui.HBox(width=W, height=h,style=ctr_style)
        lblTitle=gui.Label('Sensapex Control: VL Sep 2023',height=h,style=title_style)
        self.lblTime = gui.Label('Hello world!',height=h,style=lbl_style)
        self.lblConnection=gui.Label('Initialization',height=h,style=status_style)
        Layout_TopRow.append(lblTitle)
        Layout_TopRow.append(self.lblTime)
        Layout_TopRow.append(self.lblConnection)
        
        #position display rows
        Layout_DisplayAbsRow=gui.HBox(width=W,height=h,style=ctr_style)
        Layout_DisplayRelRow=gui.HBox(width=W,height=h,style=ctr_style)
        
        Layout_DisplayAbsRow.append(gui.Label('Abs:',width=45,height=h,style=lbl_style))
        Layout_DisplayRelRow.append(gui.Label('Rel:',width=45,height=h,style=lbl_style))
        self.POS_DISP={}
        self.RELPOS_DISP={}
        POS_LBL={}
        RELPOS_LBL={}
        for coord in ["X","Y","Z","D"]:
            self.POS_DISP[coord]=gui.Label('N/A',width=fld_w,height=h,style=lbl_style)
            POS_LBL[coord]=gui.Label(coord,height=h,width=10,style=lbl_style)
            self.RELPOS_DISP[coord]=gui.Label('N/A',width=fld_w,height=h,style=lbl_style)
            RELPOS_LBL[coord]=gui.Label(coord,height=h,width=10,style=lbl_style)
            
            Layout_DisplayAbsRow.append(POS_LBL[coord])
            Layout_DisplayAbsRow.append(self.POS_DISP[coord])   
            Layout_DisplayRelRow.append(RELPOS_LBL[coord])
            Layout_DisplayRelRow.append(self.RELPOS_DISP[coord])
            
        #Layout_PosDisplay=gui.HBox(width=W,height=h)
        
        # Controls
        # Set Home Position
        Layout_Home=gui.HBox(width=W,height=h,style=right_style)
        self.cmdSetHome=gui.Button("Set Home",height=h)
        self.cmdSetHome.onclick.do(self.on_button_pressed)
        
        self.MatlabCommunicate = gui.CheckBoxLabel('Communicate with RecStart', False, height=h, margin='50px',style=lbl_style)
        
        Layout_Home.append(self.MatlabCommunicate)
        Layout_Home.append(self.cmdSetHome)
        
        # Make a step
        Layout_Step = gui.HBox(width=W,height=h,style=left_style)
        self.cmdStep=gui.Button("Step",height=h)
        self.cmdStep.onclick.do(self.on_button_pressed)
        
        lblStep=gui.Label("Step",height=h)
        self.Step=gui.TextInput(width=fld_w*2,height=h,margin=0.5,style=inp_style)
        self.Step.set_text("100",)
        lblUnits=gui.Label("μm ",height=h,style=lbl_style,margin=20)
        
        lblStepSpeed=gui.Label("Step",height=h,style=inp_style)
        self.StepSpeed=gui.TextInput(width=fld_w*2,height=h,margin=0.5)
        self.StepSpeed.set_text("10")
        lblUnits2=gui.Label("um/s",height=h)
        
        Layout_Step.append(lblStep)
        Layout_Step.append(self.Step)
        Layout_Step.append(lblUnits)
        #Layout_Step.append(lblStepSpeed)
        #Layout_Step.append(self.StepSpeed)
        #Layout_Step.append(lblUnits2)
        
        Layout_Step.append(self.cmdStep)
        
        #Saving the data row
        
        Layout_Save=gui.HBox(width=W,height=2*h,style=left_style)
        self.Save={}
        self.Save['DirLbl']=gui.Label('Dir:',height=2*h,style=lbl_style)
        self.Save['Dir']=gui.TextInput(width=fld_w*4,height=2*h,style=inp_style)
        self.Save['Dir'].set_text("C:/Users/DeAngelis Lab/DATA/TEST/",)
        
        self.Save['SubjectLbl']=gui.Label('Subject:',height=h,style=lbl_style)
        self.Save['Subject']=gui.TextInput(width=fld_w,height=h,style=inp_style)
        self.Save['Subject'].set_text("42")
        
        self.Save['CellLbl']=gui.Label('Cell:',height=h,style=lbl_style)
        self.Save['Cell']=gui.TextInput(width=fld_w,height=h,style=inp_style)
        self.Save['Cell'].set_text("400")
        
        for k in ['DirLbl','Dir','SubjectLbl','Subject','CellLbl','Cell']:
            Layout_Save.append(self.Save[k])
        
        #Layout_bottom=gui.HBox(width=W,height=h)
        Layout=gui.VBox(width=W,height=H,style=ctr_style)
        Layout.append(Layout_TopRow)
        Layout.append(Layout_DisplayAbsRow)
        Layout.append(Layout_DisplayRelRow)
        Layout.append(Layout_Home)
        Layout.append(Layout_Step)
        Layout.append(Layout_Save)
        
        self.clock()
        self.connstate="Init"
        self.connection_loop()
        Timer(4,self.acquire).start()
        Timer(5,self.display).start()
        Timer(5,self.save).start()
        Timer(5,self.savemat).start()
        return Layout

    # listener function for all buttons
    def on_button_pressed(self, widget):
        
        if widget==self.cmdSetHome:
            self.homepos=self.pos
            self.MatlabCommunicate.set_value(True)
            
        elif widget==self.cmdStep:
            step=float(self.Step.get_text())
            speed=float(self.StepSpeed.get_text())
           
            self.jumpby(step,speed)
    def on_close(self):
        """ Overloading App.on_close event to stop the Timer.
        """
        #self.stop_flag = True
        self.flags['STOP']=True
        super(MyApp, self).on_close()




if __name__=="__main__":   
    start(SensapexUI)
   # Timer(10,stopSensapex).start()
    