import json
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel,QTextEdit, QLineEdit
import sys



SVN_Branch_Path='C:/TEMPO/MoogProtocol_VL/'
reward_folder=SVN_Branch_Path+'Reward/'
reward_settings_file=reward_folder+'reward_settings.txt'

"""with open(reward_settings_file, 'r') as file:
    reward_settings = json.load(file)
print(reward_settings)"""
reward_settings="""{
    "jackpot": "0.1",
    "mean_": "530",
    "std_": "0.5",
    "min_": "0.5",
    "max_": "1.5",
    "drdn": "0.5"
}"""
class RewardSettingsApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.layout = QVBoxLayout()
        
        #self.text_edit = QTextEdit(self)
        #self.text_edit.setText(reward_settings)
        #self.layout.addWidget(self.text_edit)
        
        self.save_button = QPushButton('Save', self)
        self.save_button.clicked.connect(self.save_settings)
        self.layout.addWidget(self.save_button)
        #self.load_button = QPushButton('Load', self)
        #self.load_button.clicked.connect(self.load_settings)
        #self.layout.addWidget(self.load_button)

        
        try:
            with open(reward_settings_file, 'r') as file:
                settings = json.load(file)
            #self.text_edit.setText(json.dumps(settings, indent=4))
            self.field_dict={}
            for key, value in settings.items():
                self.field_dict[key]=QLineEdit(self)
                self.field_dict[key].setText(str(value))
                label = QLabel(key, self)
                self.layout.addWidget(label)
                self.layout.addWidget(self.field_dict[key])
                #print(f"{key}: {value}")
            print("Settings loaded successfully.")
        except FileNotFoundError:
            print("Settings file not found.")
        except json.JSONDecodeError:
            print("Error reading settings file.")

        self.setLayout(self.layout)
        self.setWindowTitle('Reward Settings Editor')
        self.show()
        
    def save_settings(self):
        settings = {}
        for key, field in self.field_dict.items():
            settings[key] = field.text()
        settings = json.dumps(settings, indent=4)
        try:
            json.loads(settings)  # Validate JSON
            with open(reward_settings_file, 'w') as file:
                file.write(settings)
            print("Settings saved successfully.")
        except json.JSONDecodeError:
            print("Invalid JSON format.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = RewardSettingsApp()
    sys.exit(app.exec_())