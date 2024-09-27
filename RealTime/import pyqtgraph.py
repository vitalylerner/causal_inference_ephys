import numpy as np

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore

std=np.random.rand(1,384)
std2=np.random.rand(1,384)

app=pg.mkQApp("Does This Work")
win=pg.GraphicsLayoutWidget()
win.show()
win.setWindowTitle('trying')
view=win.addViewBox()
edgecolors=None
antialiasing=False
pcmi=pg.PColorMeshItem(edgecolors=edgecolors,antialiasing=antialiasing)
pcmi2=pg.PColorMeshItem(edgecolors=edgecolors,antialiasing=antialiasing)
pcmi.setPos(0,0)
pcmi2.setPos(1,0)
view.addItem(pcmi)
view.addItem(pcmi2)
textitem=pg.TextItem(anchor=(1,0))
view.addItem(textitem)
pcmi.setData(std)
pcmi2.setData(std2)
if __name__ == '__main__':
    pg.exec()