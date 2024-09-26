import pandas as pd
import numpy as np
#import datetime
#import json
import glob,os,json,datetime
import itertools# itertools handles the cycling 
import re
import multiprocessing
#pool = multiprocessing.Pool(4)

graphics=False
if graphics:
	from bokeh.plotting import figure, show,output_file, save
	from bokeh.layouts import column,row
	from bokeh.transform import linear_cmap,factor_cmap, factor_mark
	from bokeh.models import  Plot, Text,ColumnDataSource,Range1d,Legend,GroupFilter
	from bokeh.palettes import inferno, Inferno,Category10,Turbo256,Category20

	palette=Turbo256#[10]
	colors=256
