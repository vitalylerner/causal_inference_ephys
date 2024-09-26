
import os,threading,time,datetime,sys,json
from threading import Event
import pandas as pd
import pyqtgraph as pg
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtWidgets import QPushButton, QFileDialog, QLabel,QTextEdit, QLineEdit,QTabWidget
from PyQt5.QtCore import Qt,QPoint,QThread,pyqtSignal
from PyQt5.QtGui import QFont,QIcon


from pytempo_read_log import pytempo_read_log
from pytempo_miniplot import pytempo_miniplot
from pytempo_reward_casino import pytempo_reward_casino


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Behaviour/')))
from ci_functions.ci_tempo import tempo_parser,tempo_constants,ci_preprocess_db  # Replace 'some_function' with the actual function you need to import
from ci_functions.ci_analysis import ci_analysis,context


SVN_Branch_Path='C:/TEMPO/MoogProtocol_VL/'
reward_folder=SVN_Branch_Path+'Reward/'
reward_settings_file=reward_folder+'reward_settings.txt'

class FileModifiedThread(QThread):
    # Signal to emit when file is modified
    update = pyqtSignal()
    file_path=None

    def __init__(self,event,file_path):
        QThread.__init__(self)
        self.file_path=file_path
        self.stopped=event
        self.reward_last_mod_time = None


    def run(self):
        while True:
            today = datetime.date.today()
            if os.path.exists(self.file_path):
                mod_time = os.path.getmtime(self.file_path)
                if self.reward_last_mod_time is None:
                    self.reward_last_mod_time = mod_time
                    self.update.emit()
                elif mod_time != self.reward_last_mod_time:
                    self.reward_last_mod_time = mod_time
                    self.update.emit()
            time.sleep(1)  # Check every second

class pytempo_hub(QWidget):

    def __init__(self):
        super().__init__()
        self.reward_last_mod_time = None    
        self.initUI()
        stop_flag=Event()
        today = datetime.date.today()
        reward_file_name = f"Reward_{today.strftime('%y%m%d')}.csv"

        self.reward_casino=pytempo_reward_casino(reward_folder)
        self.reward_casino.roll()

        self.reward_full_path = reward_folder + reward_file_name
        self.reward_timer_thread = FileModifiedThread(stop_flag,self.reward_full_path)
        self.reward_timer_thread.update.connect(self.update_reward_progress)
        self.reward_timer_thread.start()

        behavior_file_name = "params.log"
        self.behavior_full_path = SVN_Branch_Path+ behavior_file_name
        self.behavior_timer_thread = FileModifiedThread(stop_flag,self.behavior_full_path)
        self.behavior_timer_thread.update.connect(self.update_behavior_progress)
        

        self.behavior_reader = pytempo_read_log(self.behavior_full_path) #to be replaced by ci_analysis
        self.tempo_parser = tempo_parser('C:/TEMPO/MoogProtocol_VL/','params.log')
        
        self.update_behavior_progress()
        self.behavior_timer_thread.start()

    def init_title_bar(self):
        self.setWindowTitle('pyTEMPO')
        self.setWindowFlags(Qt.FramelessWindowHint)  # Remove default title bar
                # Custom title bar
        self.title_bar = QWidget(self)
        self.title_bar.setStyleSheet("background-color: black; color: grey;")
        
        self.title_bar_layout = QHBoxLayout()
        
        self.setWindowIcon(QIcon('pytempo.ico'))


        self.title_label = QLabel("pyTEMPO", self)
        self.title_label.setFont(QFont('Courier',14,QFont.Bold))
        self.title_label.setStyleSheet("color: grey;")
        self.title_bar_layout.addWidget(self.title_label)
        
        self.close_button = QPushButton('X', self)
        self.close_button.setStyleSheet("background-color: black; color: lightgrey;")
        self.close_button.setFixedSize(20, 20)
        self.close_button.clicked.connect(self.close)
        self.title_bar_layout.addWidget(self.close_button)
        
        self.title_bar.setLayout(self.title_bar_layout)
        self.layout.addWidget(self.title_bar)
        
        self.old_pos = None

        def mousePressEvent(event):
            if event.button() == Qt.LeftButton:
                self.old_pos = event.globalPos()
        
        def mouseMoveEvent(event):
            if self.old_pos:
                delta = QPoint(event.globalPos() - self.old_pos)
                self.move(self.x() + delta.x(), self.y() + delta.y())
                self.old_pos = event.globalPos()
        
        def mouseReleaseEvent(event):
            if event.button() == Qt.LeftButton:
                self.old_pos = None

        self.title_bar.mousePressEvent = mousePressEvent
        self.title_bar.mouseMoveEvent = mouseMoveEvent
        self.title_bar.mouseReleaseEvent = mouseReleaseEvent

    def init_psycho_tab(self):
        self.analysis_tab = QWidget()
        self.analysis_layout = QVBoxLayout()
        self.axPsy = []

        for irow in range(2):
            row = QHBoxLayout()
            for icol in range(2):
                ax = pg.PlotWidget()
                ax.setFixedSize(200, 200)
                row.addWidget(ax)
                self.axPsy.append(ax)
            self.analysis_layout.addLayout(row)

        self.analysis_tab.setLayout(self.analysis_layout)
        self.tabs.addTab(self.analysis_tab, "Simple Analysis")

    def init_reward_setting_tab(self):
         # Reward Settings Tab
        self.settings_tab = QWidget()
        self.settings_layout = QVBoxLayout()
        
        
        
        # PATH OF THE MOOG Protocol FOLDER (SVN branch)
        self.path_edit = QLineEdit(self)
        self.path_edit.setText(SVN_Branch_Path)
        self.browse_button = QPushButton('Browse', self)
        self.browse_button.clicked.connect(self.browse_folder)
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("SVN Branch Path:", self))
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.browse_button)
        self.settings_layout.addLayout(path_layout)
        
        # Reward Settings
        try:
            with open(reward_settings_file, 'r') as file:
                settings = json.load(file)
                self.field_dict = {}
            for key, value in settings.items():
                self.field_dict[key] = QLineEdit(self)
                self.field_dict[key].setText(str(value))
                label = QLabel(key, self)
                label.setFixedWidth(50)
                label.setAlignment(Qt.AlignRight)
                label.setAlignment(Qt.AlignCenter)
                self.field_dict[key].setFixedWidth(50)
                hbox = QHBoxLayout()
                hbox.addWidget(label)
                hbox.addWidget(self.field_dict[key])
                self.settings_layout.addLayout(hbox)
                self.status_bar.setText("Settings loaded successfully.")
        except FileNotFoundError:
            self.status_bar.setText("Settings file not found.")
        except json.JSONDecodeError:
            self.status_bar.setText("Error reading settings file.")
        
        # Update Button
        self.save_button = QPushButton('Update Reward', self)
        self.save_button.clicked.connect(self.save_settings)
        self.settings_layout.addWidget(self.save_button)
        

        self.settings_tab.setLayout(self.settings_layout)
        self.tabs.addTab(self.settings_tab, "Reward Settings")
    def init_tabs(self) :
        
        # Create tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabBar::tab { background: darkgrey; color: white;font-family: Monospace; }")
        self.layout.addWidget(self.tabs)
        
    def init_reward_progrees_tab(self):
        self.progress_tab = QWidget()
        self.progress_layout = QVBoxLayout()
        
        self.trials_stats       = QLabel(" ", self)
        #self.correct_trials_abs = QLabel("Correct: ", self)
        #self.correct_trials_rel = QLabel("Progress 3", self)

        
        #self.progress_layout.addWidget(self.progress_label1)
        #self.progress_layout.addWidget(self.progress_label2)
        self.progress_layout.addWidget(self.trials_stats)

        self.axRewardTime = pg.PlotWidget()
        self.axRewardTime.setFixedSize(400, 200)
        self.progress_layout.addWidget(self.axRewardTime)
        #self.axRewardTime.setTitle('Reward vs Trials')
        self.axRewardTime.setLabel('left', 'Reward')
        self.axRewardTime.setLabel('bottom', 'Trials')



        #self.update_reward_progress()
        self.progress_tab.setLayout(self.progress_layout)
        self.tabs.addTab(self.progress_tab, "Reward Progress")


    
    def update_behavior_progress(self):
        now_string=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        
        try:
            self.behavior_reader.read_params()
            stats=self.behavior_reader.choice_stats()
            self.trials_stats.setText(f"Total: {stats['trials_total']}, Correct: {stats['trials_correct']} ({stats['correct_rate']}%)")

            self.tempo_parser.retrieve_meta()
            self.tempo_parser.retrieve_data()


            Dazs=context()
            Dazs.name="Dazs"
            Dazs.VIEW_DIST=36.3
            Dazs.EYE_Z    =3.5
            Dazs.IO       =3.2
            #print (Dazs)
            #print (self.tempo_parser.header['protocol'])
            if self.tempo_parser.header['protocol']=="NHP_OBJ_CI_MOTION_DETECTION":
                ci_preprocess_db(self.tempo_parser.table)
                cia=ci_analysis(Dazs,False,self.tempo_parser.table)
                flt=cia.defaultfilter()
                htxt=cia.header(flt)

                # depth psychometric curves
                DP=cia.depth_psychometric(flt,subplots=False,bFit=False)

                P=DP
                p=P[0]
                plots=list(p.plots.keys())
           
                ax=self.axPsy[0]
                ax.clear()
                for ipl,pl in enumerate(plots):
                    x=np.array(p.plots[pl].xmean.to_list())
                    y=np.array(p.plots[pl].y.to_list())
                    n=np.array(p.plots[pl].n.to_list())

                    y95low=np.array(p.plots[pl].y95low.to_list())
                    y95high=np.array(p.plots[pl].y95high.to_list())
                    ax.plot(x,y, pen='lightgrey', symbol='o', symbolBrush='darkgrey')
        
                ax.setLabel('bottom', 'disp-incr')
                ax.setLabel('left', 'prop "near"')

                MP=cia.motion_psychometric(flt,subplots=False,bFit=False)

                P=MP
                p=P[0]
                plots=list(p.plots.keys())
           
                ax=self.axPsy[1]
                ax.clear()
                for ipl,pl in enumerate(plots):
                    x=np.array(p.plots[pl].xmean.to_list())
                    y=np.array(p.plots[pl].y.to_list())
                    n=np.array(p.plots[pl].n.to_list())

                    y95low=np.array(p.plots[pl].y95low.to_list())
                    y95high=np.array(p.plots[pl].y95high.to_list())
                    ax.plot(x,y, pen='lightgrey', symbol='o', symbolBrush='darkgrey')
        
                ax.setLabel('bottom', 'obj-amp')
                ax.setLabel('left', 'prop "moving"')

                if False:
                    x=self.tempo_parser.table.obj_amp
                    y=self.tempo_parser.table.ret_amp
                    ax=self.axPsy[3]
                    ax.clear()
                    ax.plot(x, y, pen=None, symbol='d', symbolBrush=pg.mkBrush(50, 50, 50, 25))  # 25 is the alpha value (0.1 * 255)
                    ax.setLabel('left', 'retinal amplitude')
                    ax.setLabel('bottom', 'world amplitude')

            #print (self.tempo_parser.table.head())
            #self.miniplot.plot(protocol=154,type='depth',D=self.behavior_reader.D)
        except ZeroDivisionError:
            self.trials_stats.setText("No trials yet.")
        except FileNotFoundError:
            self.status_bar.setText("No trials yet.")
        
        
        #self.status_bar.setText("Behavior file updated."+now_string)

    def randomize_reward(self):
        pass

    def update_reward_progress(self):
        full_path = self.reward_full_path
        self.axRewardTime.clear()
        rew_des =  pg.InfiniteLine(pos=400, angle=0, pen=pg.mkPen("#005500", width=2, alpha=0.5),label='daily minimum',labelOpts={'position': 0.8, 'color':(20,60,20),'movable':True})
        rew_suff = pg.InfiniteLine(pos=250, angle=0, pen=pg.mkPen("#333300", width=2, alpha=0.5), label='motivation',  labelOpts={'position': 0.9, 'color': (80, 80, 20), 'movable': True})
        self.axRewardTime.addItem(rew_des)
        self.axRewardTime.addItem(rew_suff)
        self.axRewardTime.plot([0, 1000], [0, 400], pen=pg.mkPen("#002200", width=2,alpha=0.2))
        try:
            data = pd.read_csv(full_path)
            if not data.empty:
                self.axRewardTime.plot(data.index, data.iloc[:, -1]*0.001, pen=pg.mkPen('lightgrey', width=2))
                r=self.reward_casino.roll()

            else:
                self.status_bar.setText("Reward file is empty.")
        except FileNotFoundError:
            self.status_bar.setText("Reward file not found.")
        except pd.errors.EmptyDataError:
            self.status_bar.setText("Reward file is empty.")
        except Exception as e:
            self.status_bar.setText(f"Error updating reward progress: {e}")
        self.axRewardTime.setYRange(0, 500)
        self.axRewardTime.setXRange(0, 1300)

    def initUI(self):
        

        self.setStyleSheet("background-color: black; color: lightgrey;font-family:Courier;")
        #self.setGeometry(0, QApplication.desktop().screenGeometry().height() - self.height(), self.width(), self.height())
        screen_geometry = QApplication.desktop().screenGeometry()
        

        self.status_bar = QLabel(self)
        self.layout = QVBoxLayout()

        self.init_title_bar()
        self.init_tabs()
        self.init_reward_setting_tab()
        self.init_reward_progrees_tab()
        self.init_psycho_tab()
        #self.update_reward_progress()
                # Status Bar
        self.layout.addWidget(self.status_bar)
        
        self.setLayout(self.layout)
        self.setGeometry(screen_geometry.width() - self.width(), 0, self.width(), self.height())

        
        self.show()
        
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select SVN Branch Path', self.path_edit.text())
        if folder:
            self.path_edit.setText(folder)
            global SVN_Branch_Path
            SVN_Branch_Path = folder
            global reward_folder
            reward_folder = SVN_Branch_Path + '/Reward/'
            global reward_settings_file
            reward_settings_file = reward_folder + 'reward_settings.txt'
            self.status_bar.setText(f"SVN Branch Path updated to: {SVN_Branch_Path}")

    def save_settings(self):
        settings = {}
        for key, field in self.field_dict.items():
            settings[key] = field.text()
        settings = json.dumps(settings, indent=4)
        try:
            json.loads(settings)  # Validate JSON
            with open(reward_settings_file, 'w') as file:
                file.write(settings)
            self.status_bar.setText("Settings saved successfully.")
        except json.JSONDecodeError:
            self.status_bar.setText("Invalid JSON format.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = pytempo_hub()
    sys.exit(app.exec_())