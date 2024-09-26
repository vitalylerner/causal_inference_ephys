# -*- coding: utf-8 -*-
"""
Created on Thu May 16 09:50:11 2024
Graphical presentation of the analysis of 
Causal Inference data

@author: Vitaly Lerner

requirements: numpy pandas bokeh selenium

The renderer of choice is bokeh

"""
from bokeh.plotting import figure, show,output_file, save
from bokeh.layouts import column,row
from bokeh.transform import linear_cmap,factor_cmap, factor_mark
from bokeh.models import  Plot, Text,ColumnDataSource,Range1d,Legend
from bokeh.models import NumeralTickFormatter, GroupFilter,Label
from bokeh.colors import RGB
from bokeh.palettes import Inferno256,Turbo256

from ci_functions.ci_analysis import sigmoid, inversegauss

import pandas as pd
import numpy as np 
class ci_graphics:
    """Causal Inference graphic functions
    
    """
    G=None
    
    g_params_default={
        'fig_xy': {'width':250,'height':250,'toolbar_location':None},
        'plot_xy':{'color':'black','marker':'diamond'},
        'fig_psy': {'height':250,'width':300,'toolbar_location':None,'y_range':[-0.1,1.1]},
        'plot_psy': {}
        }
    ax_params=None
    g_params=None
    def __init__(self,scheme:str='Default'):
        self.g_params=pd.read_excel('Settings/graphics.xls',sheet_name='Plots')
        self.ax_params=pd.read_excel('Settings/graphics.xls',sheet_name='Axes')
        self.g_params.replace(np.nan,'',inplace=True)
        
    def header(self,txtHeader:str):
        fSummary=figure(width=1200,height=100,output_backend='svg',toolbar_location=None)
        statslabel = Label(x=10, y=10, 
                           x_units='screen', y_units='screen',
                           text=txtHeader,text_align='left',
                           text_color="black",text_alpha=0.8,text_font_size='9pt')

        fSummary.add_layout(statslabel)
        return fSummary
    def scatter(self,D:pd.DataFrame):
        """Plot 2d data based on two first columns of a table.
        
        input: 
            D: table (pandas dataframe), at least two columns
            figargs: arguments to be passed to figure 
        
        output:
            bokeh figure handle
        """
        cols=D.columns.to_list()
        fig_args={'width':400,'height':400,'toolbar_location':'below'}# self.g_params['fig_xy']
        plot_args={}#self.g_params['plot_xy']
        
        f=figure(x_axis_label=cols[0],y_axis_label=cols[1],output_backend='svg',**fig_args)
        a=min(200./len(D),0.5)
        f.scatter(x=cols[0],y=cols[1],source=D,alpha=a,**plot_args)
        return f
    
    
    def plot_psychometric_curves(self,P:list):
        
        P=[p for p in P if not (p is None)]
        F=[None for p in P]
        
        #fig_args=self.g_params['fig_psy']
        #plot_args=self.g_params['plot_psy']
        fig_args={'width':400,
                  'height':400,'output_backend':'svg',
                  'toolbar_location':'below'
                 }
        for ifigure,p in enumerate(P):
            # Figure decorations
            f=figure(**fig_args)
            f.toolbar.logo = None
            f.yaxis.ticker=[0.0,0.25,0.5,.75,1.0]
            f.yaxis.major_label_overrides = {0.0: '0', 0.25: '', 
                                             0.5: '50%', 0.75:'', 
                                             1.0:'100%'}
            f.y_range=Range1d(-0.1,1.1)
            sz='12pt'
            f.title.text_font_size=sz
            for obj in [f.xaxis,f.yaxis]:
                obj.axis_label_text_font_size=sz
                obj.major_label_text_font_size=sz
                obj.major_label_text_font_size=sz
            f.axis.major_tick_out = 0
            f.axis.major_tick_in = -5
            f.axis.major_label_standoff=10
            
            #xlabel scaling and decorations
            xlabel0=p.x_label
            A=self.ax_params
            decorate_x=xlabel0 in A['category'].to_list()
            if decorate_x:
                a=A[A['category']==xlabel0].iloc[0]
                
                xlabel=a.alias                
                if p.x_label_visible:
                    f.xaxis.axis_label=xlabel
                else:
                    f.xaxis.axis_label=""
                tk=np.arange(a.ticks_min,
                             a.ticks_max+a.ticks_step,
                             a.ticks_step)
                f.xaxis.ticker=tk
                tl={}
                for n in tk:
                    tl[n]=f"{n:{a.format}}"+a.units
                f.xaxis.major_label_overrides=tl
                x_mult=a.multiplier
                
            else:
                x_mult=1.0
            
            #Y axis decorations
            if p.y_label_visible:
                f.yaxis.axis_label=p.y_label
            else:
                f.yaxis.axis_label=""

                
                
            xmin=10000
            xmax=0
            plots=list(p.plots.keys())
            for ipl,pl in enumerate(plots):
                #f.line(x='xmean',y='y',source=p.plots[pl],color=self.ci_colors[pl])
                g=self.g_params[self.g_params['category']==pl].iloc[0]
                
                color=RGB(g.color_r,g.color_g,g.color_r,g.alpha)
                marker=g.marker
                size=g.size
                
                x=np.array(p.plots[pl].xmean.to_list())
                y=np.array(p.plots[pl].y.to_list())
                n=np.array(p.plots[pl].n.to_list())
                y95low=np.array(p.plots[pl].y95low.to_list())
                y95high=np.array(p.plots[pl].y95high.to_list())
                
                # Treating fits
                if pl in  p.fits.keys():
                    if decorate_x:
                        xmin=a.range_min
                        xmax=a.range_max+0.1
                       
                    else:
                        xmin=x.min()
                        xmax=x.max()
                    
                    
                    xstep=(xmax-xmin)*0.001
                    xfit=np.arange(xmin,xmax,xstep)
                    
                    fmean=p.fits[pl]['p_mean']
                    flo  =p.fits[pl]['p_lo']
                    fhi  =p.fits[pl]['p_hi']
                    func=p.fits[pl]['function']
                    if func=='sigmoid':
                        c_f=sigmoid
                        yf_mean=np.array([c_f(xfit_,fmean[0],fmean[1]) for xfit_ in xfit])
                        yf_lo=np.array([c_f(xfit_,flo[0],flo[1]) for xfit_ in xfit])
                        yf_hi=np.array([c_f(xfit_,fhi[0],fhi[1]) for xfit_ in xfit])
                    elif func=='inversegauss':
                        c_f=inversegauss
                        yf_mean=np.array([c_f(xfit_,fmean[0],fmean[1],fmean[2],fmean[3]) for xfit_ in xfit])
                        yf_lo=np.array([c_f(xfit_,flo[0],flo[1],flo[2],flo[3]) for xfit_ in xfit])
                        yf_hi=np.array([c_f(xfit_,fhi[0],fhi[1],fhi[2],fhi[3]) for xfit_ in xfit])
                    
                    """f.varea(xfit*x_mult,yf_lo,yf_hi,
                            alpha=0.2,
                            fill_color=color,
                            hatch_pattern=g.hatch_pattern,
                            hatch_color=color,
                            hatch_alpha=0.2)"""
                    fit_color=RGB(g.color_r,g.color_g,g.color_b,g.fit_alpha)
                    f.line(xfit*x_mult,yf_mean,
                           color=fit_color,
                           line_dash=g.fit_line,
                           line_width=2)
                #!!! END OF Treating fits
                else:
                    f.line(x=p.plots[pl].xmean*x_mult,
                           y=p.plots[pl].y,line_color=color,line_dash=g.fit_line,line_width=2) 

                #!!! Plot the data!
                if decorate_x:
                    if marker=='triangle':
                        #print(a)
                        f.triangle(x=p.plots[pl].xmean*a.multiplier,
                              y=p.plots[pl].y,
                              angle_units='deg',
                              angle=g.rotate,
                              size=size,
                              line_color=color,
                              color=color)
                    else:
                        f.scatter(x=p.plots[pl].xmean*a.multiplier,
                              y=p.plots[pl].y,
                              marker=marker,
                              size=size,
                              color=None)
                    
                else:
                    f.scatter(x='xmean',y='y',source=p.plots[pl],
                          marker=marker,
                          size=size,
                          line_color=color,
                          line_dash=g.fit_line,
                          color=None)
            
                    


                #!!! plot the confidence intervals
                try:
                    if decorate_x:
                        for (px,p95l,p95h) in zip(x,y95low,y95high):
                            f.line([px*a.multiplier]*2,[p95l,p95h],color=color,
                                   line_width=2,line_alpha=0.5)
                            f.scatter([px*a.multiplier]*2,[p95l,p95h],color=color,marker='dash',size=5)
                    else:
                        for (px,p95l,p95h) in zip(x,y95low,y95high):
                            f.line([px]*2,[p95l,p95h],color=color)
                       
                except TypeError:
                    pass
                
                            
                    #f.line(xfit,yf_lo,line_)
                    #f.line(xfit,yf_hi,line_color=self.ci_colors[pl])
                    
                    #for (px,py,pstd) in zip(x,y,ystd):
                    #    f.line([px]*2,[py-pstd*0.5,py+pstd*0.5],color=self.ci_colors[pl])
                #xmin,xmax=p.plots[pl].xmean.min(),p.plots[pl].xmean.max()
                

                xmin=np.min([xmin,p.plots[pl]['xmean'].min()])
                xmax=np.max([xmax,p.plots[pl]['xmean'].max()])

            for ipl,pl in enumerate(plots):
                g=self.g_params[self.g_params['category']==pl].iloc[0]
                
                color=RGB(g.color_r,g.color_g,g.color_r,g.alpha)
                
                n=p.plots[pl].n.sum()
                n_pos_x=xmin+(xmax-xmin)*0.9
                n_pos_y=0.2*ipl
                
                statslabel = Label(x=n_pos_x*x_mult, y=n_pos_y, 
                                   x_units='data', y_units='data',
                                   text=f'n={n}',text_align='right',
                                   text_color=color,text_alpha=0.5,text_font_size='8pt')

                f.add_layout(statslabel)
                #if decorate_x:
                    
            xrange=np.array([xmin,xmax])
            if decorate_x:
                xrange=np.array([a.ticks_min,a.ticks_max])
            f.x_range=Range1d(xrange[0],xrange[1])
            #f.line(xrange*x_mult,xrange*0+0.5,color=RGB(0.2,0.2,0.2,0.2),width=2)
            f.title=p.name
            
            F[ifigure]=f
        return row(F)

if __name__=="__main__":
    
    raise ValueError("This is wrong scope, do not run this file directly")