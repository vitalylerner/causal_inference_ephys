"""
Offline analysis of Causal Inference behavioural data.

@author Vitaly
@created 2024

@requirements



"""
import pandas as pd
import numpy as np
import scipy.stats as st 
from scipy.stats import binomtest
from scipy.optimize import curve_fit

from ci_functions.ci_tempo   import ci_import_from_db
from ci_functions.ci_binning import ci_binning

"""
************************************************************************
Distance: cm
Angles  : deg
************************************************************************
"""
#def wilson_ci(k,n):
def sigmoid(x, a0, a1):
     return 1.0 / (1.0 + np.exp(-(x-a0)/a1))
def inversegauss(x,a0,a1,a2,a3):
     return   a2-a3*np.exp(-(x-a0)**2/(2.*a1**2))
 
class context:
    """Stores geometric features of the subject.
    
    -
    """
    
    VIEW_DIST = -1.0
    IO        = -1.0
    EYE_Z     = -1.0
    EYE_Y     = -1.0
    name      = ""
    def __init__(self):
        pass	
    def __str__(self):
        """Cast the object to string."""
        a = '--------------\n'
        a += self.name + '\n'
        a += "VIEW_DIST = {:.2f}".format(self.VIEW_DIST) + '\n'
        a += "IO        = {:.2f}".format(self.IO) + '\n'
        a += "EYE_Z     = {:.2f}".format(self.EYE_Z) + '\n'
        a += '--------------\n'
        return a
    
def ret_amp(disp_incr,self_amp,obj_amp,VIEW_DIST,EYE_Z,IO):
    """Fundamental geometric function."""

    D=VIEW_DIST-EYE_Z
    #print ('2',IO,VIEW_DIST,EYE_Z,D,disp_incr)
    deltaD=0.5*IO/np.tan(np.arctan(0.5*IO/D)+0.5*np.deg2rad(disp_incr))-D
    th_fp=-np.arctan(self_amp/D)
    th_obj=np.arctan( obj_amp/D-self_amp/(D+deltaD))
    r_amp=-np.rad2deg(th_obj-th_fp)
    #print ('6')
    return r_amp
    
class ci_psychometric_set:
    """
    Causal Inference (but not only) psychometric plots data.
    
    Stores data and graphic parameters for a set of psychometric curves
    grouped together
    """
    
    plots={}
    fits={}
    name=""
    xaxis_label=""
    xaxis_label_visible=False
    yaxis_label=""
    yaxis_label_visible=False
    meta=None
    
    def fit(self,func):
        ks=list(self.plots.keys())
        fits={}
        if func=='sigmoid':
            c_f=sigmoid
            
            bounds=([-2.0,0.001],[2.0,10.0])
            
        elif func=='inversegauss':
            #a2-a3*np.exp(-(x-a0)**2/(2.*a1**2))
            c_f=inversegauss
            bounds=([-2.0,0.001,0.5,0.3],[2.0,10.0,1.05,1.05])
        for k in ks:
            p=self.plots[k]
            x=p.xmean
            
            if len(x)>3:
                y=p.y
                rng=~np.isnan(x+y)
                x=x[rng]
                y=y[rng]
                ylow=p.y95low[rng]
                yhi =p.y95high[rng]
                try:
                    popt, pcov = curve_fit(c_f, x,y, bounds=bounds)
                    
                    
                    poptlow,pcov=curve_fit(c_f,x,y)
                    popthi,pcov=curve_fit(c_f,x,y)
                    fits[k]={'function':func,'p_mean':popt,'p_lo':poptlow,'p_hi':popthi}
                except RuntimeError:
                    xx=np.array(list(x)*3)
                    yy=np.array(list(y)+list(ylow)+list(yhi))
                    popt,pcov=curve_fit(c_f,xx,yy,bounds=bounds)
                    poptlow=popt
                    popthi=popt
                    fits[k]={'function':func,'p_mean':popt,'p_lo':poptlow,'p_hi':popthi}
                    pass
        self.fits=fits
    def __init__(self,plots:dict,meta:dict={},name:str="",
                 x_label:str="",x_label_visible:bool=False,
                 y_label:str="",y_label_visible:bool=False):
        """
        
        Initialize.

        Parameters
        ----------
        plots : dict
            DESCRIPTION.
        name : str, optional
            DESCRIPTION. The default is "".
        x_label : str, optional
            DESCRIPTION. The default is "".
        x_label_visible : bool, optional
            DESCRIPTION. The default is False.
        y_label : str, optional
            DESCRIPTION. The default is "".
        y_label_visible : bool, optional
            DESCRIPTION. The default is False.

        Returns
        -------
        None.

        """
        self.plots=plots
        self.name=name
        self.y_label=y_label
        self.y_label_visible=y_label_visible
        
        self.x_label=x_label
        self.x_label_visible=x_label_visible
        self.meta=meta
    def __str__(self):
        """Cast to string for displaying."""
        s=self.name
        s+=f' {len(self.plots)} plots'
        return s

class ci_analysis():
    """Causal Inference Analyses.
    
    Psychometric curves
    Conditional psychometric curves
    and more
    """
    
    D=None
    CAT={}
    context=None
    
    #Filters=['NonInstructional',]
    
    def calculate_retinal_motion (self):
        """Calculate retinal motion based on context and conditions."""
        obj_amp  = np.array(self.D.obj_amp.to_list())
        disp_incr= np.array(self.D.disp_incr.to_list())
        self_amp = np.array(self.D.self_amp.to_list())
        
        c=self.context
        self.D['ret_amp']=ret_amp(disp_incr,self_amp,obj_amp,c.VIEW_DIST,c.EYE_Z,c.IO)

    def calculate_motion_sign(self):
        """Calculate whether self motion and object motion are in the same direction."""
        obj_amp  = np.array(self.D.obj_amp.to_list())
        self_amp = np.array(self.D.self_amp.to_list())
        
        self.D['motion_sign']=np.sign(obj_amp*self_amp)
        self.D['self_amp_sign']=np.sign(self_amp)
        self.D['obj_amp_sign']=np.sign(obj_amp)
        
        
    def __init__(self,cntxt:context,autoimport:bool=True,D:pd.DataFrame=None):
        if autoimport:
            self.D=ci_import_from_db()
        else:
            self.D=D
        
        self.CAT['obj_amp']     = {'field':'obj_amp','units':'cm','signlike':False}
        self.CAT['disp_incr']   = {'field':'disp_incr','units':'deg','signlike':False}
        self.CAT['ret_amp']     =  {'field':'ret_amp','units':'deg','signlike':False}
        self.CAT['self_amp_sign'] = {'field':'self_amp_sign','units':'cm','signlike':True}
        self.CAT['obj_amp_sign']  ={'field':'obj_amp_sign','units':'cm','signlike':True}
        self.CAT['motion_sign'] =  {'field':'motion_sign','units':'','signlike':True}
        self.CAT['choice_near'] = {'field':'choice_near','units':'','signlike':True}
        self.CAT['choice_moving']={'field':'choice_moving','units':'','signlike':True}
        self.CAT['vert_disp']    ={'field':'vert_disp','units':'cm','signlike':False}
        
        self.context=cntxt
        self.calculate_retinal_motion()
        self.calculate_motion_sign()
        
    def listsessions(self,flt=None):
        """Return list of all sessions in the dataset."""
        if flt is None:
            return sorted(list(set(list(self.D['session']))))
        else:
            return sorted(list(set(list(self.D[flt]['session']))))
        
    def rowfilter(self,fltName:str='',fltData=None):
        """
        Create filter for the dataframe D based on the filtername and additional parameters.

        Parameters
        ----------
        fltName : str, optional
            DESCRIPTION. The default is ''.
        fltData : TYPE, optional
            DESCRIPTION. The default is None.

        Returns
        -------
        flt : list of boolean [length of self.D]
            for each row in self.D 
        """
        
        D=self.D
        flt=[True for i in range(len(D))]
        if fltName=='outcome':
            flt=(D['outcome']==5) | (D['outcome']==0)
        elif fltName=='instructional':
            bInstr=fltData
            flt=D['instructional']==bInstr
        elif fltName=='task':
            tasknum=fltData
            flt=D['task']==fltData
        elif fltName == 'x':
            left=min(fltData[0],fltData[1])
            right=max(fltData[0],fltData[1])
            flt=(D['start_x']<=right) & (D['start_x']>=left)
        elif fltName == 'nonstat':
            flt=D.motion_sign.abs()>0.0
        elif fltName in ['choice_near','choice_moving']:
            if fltData:
                flt=D[fltName]
            else:
                flt=~D[fltName]
        elif fltName in ['self_amp_sign','motion_sign']:
            flt=D[fltName]==float(fltData)
            
        elif fltName in ['y','obj_amp','disp_incr','session','vert_disp_sigma']:
            if type(fltData) in [int,float,np.float64,np.float32]:
                flt=D[fltName]==fltData
            else:
                s_from=min(fltData[0],fltData[1])
                s_to  =max(fltData[0],fltData[1])
                flt=(D[fltName]>s_from) & (D[fltName]<=s_to)

            
        return flt
    
    def defaultfilter(self):
        f =self.rowfilter('outcome') 
        f &=  self.rowfilter ( 'instructional',False) 
        return f
    
  
    
    def psychometric_curve(self,x:str,y:str,flt:list=None):
        """
        Generate psychometric curve based on the filter and binning parameters.

        Parameters
        ----------
        x : str
            name of the column that serves as the variable.
        y : str
            name of the column that serves as the choice.
        flt : list of booleans, optional
            filters the rows of the dataframe
        bins : int or list of float, optional
            if int:
                if 0(default): number of bins is set to 10
                if n: number of bins is set to n
            if list of floats:
                the bins are set exactly to bins
        zero_discrete : bool, optional
            Binning parameter, ignored if bins is int
            True: create a special bin for 0 as a discrete number
            False: don't treat 0 as a special discrete case
        symm : int, optional
            Binning parameter, ignored if bins is list of floats
            True: enforce symmetry around 0

        Returns
        -------
        DataFrame with four columns: 
            xleft: bins left boundary
            xright: bins right boundary
            xmean: bins center (averaged over all trails in the bin)
            y: choice probability
        """
        #
        
        temp_D=self.D[flt][[x,y]].copy()
        D=pd.DataFrame({'x':temp_D[x],'y':temp_D[y]})
    
        u_vals=sorted(list(set(D.x.to_list())))
        n_uvals=len(u_vals)
        def int_low(X):
            
            #r=[binomtest(p=x). for x in X]
            #k=np.sum(X)
            #n=len(X)
            return binomtest(np.sum(X),len(X)).proportion_ci().low
            #return np.mean(X)-np.std(X)*0.5
            #return 
        def int_high(X):
            #int_all=st.t.interval(alpha=0.8, df=len(X)-1, 
            #                  loc=np.mean(X), 
            #                  scale=st.sem(X)) 
            #return int_all[1]
            return binomtest(np.sum(X),len(X)).proportion_ci().high
        if len(D)<5:
            xvals=np.array(D.x)
            yvals=np.array(D.y,dtype=float)
            ycnt=0.*yvals+1.
            ystd=0.*yvals
            
            y95low=yvals*1.
            y95high=yvals*1.
        else:    
            if n_uvals<14:
                D_pivot = pd.pivot_table(D,index='x',values='y',aggfunc={'y':['mean','count']})
                
                xvals   =  np.array(D_pivot.index.to_list())
                yvals   = np.array((D_pivot[['mean']]['mean']).to_list())
                ycnt    = np.array((D_pivot[['count']]['count']).to_list())
                y95low= [binomtest(int(yval*ycnt_),ycnt_).proportion_ci().low  for yval,ycnt_ in zip(yvals,ycnt)]
                y95high=[binomtest(int(yval*ycnt_),ycnt_).proportion_ci().high for yval,ycnt_ in zip(yvals,ycnt)]

            else:
                x=np.array(D.x.to_list())
                q=7

                cat=pd.qcut(x,q,duplicates='drop')
                D_group=D.groupby(cat)
                
                yvals=np.array(D_group.y.mean().to_list())
                ycnt =np.array(D_group.y.count().to_list())
                xvals=np.array(D_group.x.mean().to_list())
                try:
                    y95low= [binomtest(int(yval*ycnt_),ycnt_).proportion_ci().low  for yval,ycnt_ in zip(yvals,ycnt)]
                    y95high=[binomtest(int(yval*ycnt_),ycnt_).proportion_ci().high for yval,ycnt_ in zip(yvals,ycnt)]
                except ValueError:
                    y95low=0*yvals
                    y95high=0*yvals
                    for i in range(len(yvals)):
                        try:
                            y95low[i]= binomtest(int(yvals[i]*ycnt[i]),ycnt).proportion_ci().low
                            y95high[i]= binomtest(int(yvals[i]*ycnt[i]),ycnt).proportion_ci().high
                        except :
                            y95low[i]=yvals[i]
                            y95high[i]=yvals[i]

    

        P=pd.DataFrame({'xmean':xvals,'y':yvals,'n':ycnt,'y95low':y95low,'y95high':y95high})
        return P
    

    def header(self,flt=None):
        #print ("HERE!")
        if flt is None:
            flt=[True for i in range(len(self.D))]
            
        fltCorrect=flt & self.D.correct
        correct_grand=int(100*np.sum(fltCorrect)*1./np.sum(flt))
        tasks=list(set(self.D[flt]['task'].to_list()))
        TASKS={0:'Dual',1:'Motion',2:'Depth'}
        tasks=','.join([TASKS[t] for t in tasks])
        
        try:
            Sessions=self.listsessions(flt)
        except KeyError:
            Sessions=[-1]
        txt='Causal Inference: '+tasks+'\n'
        txt+="Sessions: "+f"{Sessions}"[1:-1]+'\n'
        txt+=f'{len(self.D[flt])} trials, {correct_grand}% correct'
        return txt
        
      
    def conditional_depth(self,flt=None,confidence_threshold:float=0.3):
        flt &=  self.rowfilter('nonstat')
        P=self.motion_psychometric(flt)
        nplots=len(P)-1
        flt_select=[False for i in range(len(self.D))]
        
        for p in P[1:]:
            disp_incr=p.meta['disp_incr']
            ks=list(p.plots.keys())
            for sgn in [-1.0,1.0]:
                k=f"self_amp_sign={sgn}"
                if k in ks:
                    p_self=p.plots[k][ (p.plots[k].y-0.5).abs() < confidence_threshold]

                    if (len(p_self)>0) :
                        flt_dispincr=self.rowfilter('disp_incr',disp_incr)
                        flt_selfamp=self.rowfilter('self_amp_sign',sgn)
                        for obj_amp in p_self.xmean.to_list():
                            flt_objamp=self.rowfilter('obj_amp',obj_amp)
                            
                            flt_=flt & flt_objamp & flt_selfamp & flt_dispincr
                            flt_select|=flt_

        P2=self.build_psychometric(cat1str='disp_incr', 
                                  cat2str='motion_sign',
                                  cat3str= "choice_moving",
                                  choicestr='choice_near',
                                  choicealias='prop "near"',
                                  flt=flt_select)
        return P2
    
        
    def conditional_motion(self,flt=None,confidence_threshold:float=0.3):
        flt &=  self.rowfilter('nonstat')
        P=self.depth_psychometric(flt)
        nplots=len(P)-1
        flt_select=[False for i in range(len(self.D))]
        
        for p in P[1:]:
            obj_amp=p.meta['obj_amp']
            ks=list(p.plots.keys())
            for sgn in [-1.0,1.0]:
                k=f"self_amp_sign={sgn}"
                if k in ks:
                    p_self=p.plots[k][ (p.plots[k].y-0.5).abs() < confidence_threshold]

                    if (len(p_self)>0) :
                        flt_objamp=self.rowfilter('obj_amp',obj_amp)
                        flt_selfamp=self.rowfilter('self_amp_sign',sgn)
                        for disp_incr in p_self.xmean.to_list():
                            flt_dispincr=self.rowfilter('disp_incr',disp_incr)
                            
                            flt_=flt & flt_objamp & flt_selfamp & flt_dispincr
                            flt_select|=flt_

        P2=self.build_psychometric(cat1str='obj_amp', 
                                  cat2str='motion_sign',
                                  cat3str='choice_near',
                                  choicestr='choice_moving',
                                  choicealias='prop "moving"',
                                  flt=flt_select)
        return P2
    
    def conditional_motion_retinal(self,flt=None,confidence_threshold:float=0.3):
        flt &=  self.rowfilter('nonstat')
        P=self.depth_psychometric(flt)
        nplots=len(P)-1
        flt_select=[False for i in range(len(self.D))]
        
        for p in P[1:]:
            obj_amp=p.meta['obj_amp']
            ks=list(p.plots.keys())
            for sgn in [-1.0,1.0]:
                k=f"self_amp_sign={sgn}"
                if k in ks:
                    p_self=p.plots[k][ (p.plots[k].y-0.5).abs() < confidence_threshold]

                    if (len(p_self)>0) :
                        flt_objamp=self.rowfilter('obj_amp',obj_amp)
                        flt_selfamp=self.rowfilter('self_amp_sign',sgn)
                        for disp_incr in p_self.xmean.to_list():
                            flt_dispincr=self.rowfilter('disp_incr',disp_incr)
                            
                            flt_=flt & flt_objamp & flt_selfamp & flt_dispincr
                            flt_select|=flt_

        P2=self.build_psychometric(cat1str='ret_amp', 
                                  cat2str='motion_sign',
                                  cat3str='choice_near',
                                  choicestr='choice_moving',
                                  choicealias='prop "moving"',
                                  flt=flt_select)
        return P2

    def vert_disp_psychometric(self,flt=None):
        P= self.build_psychometric('disp_incr','','vert_disp_sigma',
                                       'choice_near','prop "near"',flt)
        for ip, p in enumerate(P):
            p.fit('sigmoid')
        return P
    
    
    def retinal_motion_psychometric(self,flt=None,subplots:bool=True):
        """Motion Psychometric curve in retinal coordinates (degrees)."""
        if subplots:
            P= self.build_psychometric('ret_amp','disp_incr','self_amp_sign',
                                           'choice_moving','prop "moving"',flt)
        else:
            P= self.build_psychometric('ret_amp','','self_amp_sign',
                                           'choice_moving','prop "moving"',flt)
        for ip, p in enumerate(P):
            p.fit('inversegauss')
        return P
    
    def motion_psychometric(self,flt=None,subplots:bool=True,bFit:bool=True):
        """Motion Psychometric curve in world coordinates (cm)."""
        if subplots:
            P=self.build_psychometric('obj_amp','disp_incr','self_amp_sign',
                                           'choice_moving','prop "moving"',flt)
        else:
            P=self.build_psychometric('obj_amp','','self_amp_sign',
                                           'choice_moving','prop "moving"',flt)
        if bFit:
            for ip,p in enumerate(P):
                p.fit('inversegauss')
        return P
    def depth_psychometric(self,flt=None,subplots:bool=True,bFit:bool=True):
        """Depth Psychometric curve."""
        if subplots:
            P=self.build_psychometric('disp_incr','obj_amp','self_amp_sign',
                                           'choice_near','prop "near"',flt)
        else:
            P=self.build_psychometric('disp_incr','','self_amp_sign',
                                           'choice_near','prop "near"',flt)
        if bFit:
            for ip, p in enumerate(P):
                p.fit('sigmoid')
        return P
    
    def world_retinal(self,flt=None):
        """Table for Scatter Parametric space (obj-amp,ret-amp)."""
        if flt is None:
            flt=[True for r in range(len(self.D))]
        D=self.D[flt][['obj_amp','ret_amp']].copy().rename({'obj_amp':'x','ret_amp':'y'},inplace=True)
        return D
        
                      
    def build_psychometric(self,cat1str:str,cat2str:str,cat3str:str,choicestr:str,choicealias:str,flt=None):
        """Set of psychometric curves.
        
        cat1: point-to-point within the line (x-axis) category
        cat2: axes-to-axes category, if '' then only one axes is created
        cat3: line-to-line within axes category
        
        """
        def build_panel(f):
            plots={}
            if cat3str in ['self_amp_sign','motion_sign','obj_amp_sign']:
                flt_names=[cat3str]*3
                flt_data =[-1.0,0.0,1.0]
            elif cat3str in ['choice_near','choice_moving']:
                flt_names = [cat3str]*2
                flt_data  = [True,False]
            elif cat3str=='vert_disp_sigma':
                flt_data=np.array(sorted(list(set(self.D.vert_disp_sigma.to_list()))))
                flt_names = [cat3str]*len(flt_data)
                flt_names=[cat3str]*3
                flt_data= [0.0,[0.05,1.05]]
            for s,d in zip(flt_names,flt_data):
                
                f_ =f & self.rowfilter(s,d)
                if np.array(d).size==1:
                    catstr=s+f'={d}'
                else:
                    catstr=s+f' in {d[0],d[1]}'
                
                if sum(f_)>0:
                    cat1['values']=list(self.D[f_][cat1['field']])                    
                    cat1['bins']=ci_binning(cat1['values'])
                    plots[catstr]=self.psychometric_curve(cat1['field'],choicestr,flt=f_)
                    
            return plots
        cat1=self.CAT[cat1str]
        
        
        f2 = self.defaultfilter()
        #f2 &=  self.rowfilter ( 'task',0)
        if not (flt is None):
            f2 &= flt

        p=build_panel(f2)
        P_main=ci_psychometric_set(p,"",
                              x_label=f'{cat1["field"]}({cat1["units"]})',x_label_visible=True,
                              y_label=choicealias,y_label_visible=True)

        if not cat2str=='':
            cat2=self.CAT[cat2str]
            cat2['values']=list(self.D[f2][cat2['field']])
            cat2['bins']=ci_binning(cat2['values']) 
            
            P=[None for i in range( len(cat2['bins'].bins)+1 )]
            P[0]=P_main
            for i in range(len(cat2['bins'].bins)):
                val=float(cat2['bins'].bins[i])
                f3=f2 & self.rowfilter( cat2['field'],  val)
                p=build_panel(f3)
                if not (p=={}):
                    meta={cat2['field']:val}
                    P[i+1]=ci_psychometric_set(p,
                                      name=f"{cat2['field']}:{val:.1f}{cat2['units']}",
                                      meta=meta,
                                      x_label=f'{cat1["field"]}({cat1["units"]})',x_label_visible=False,
                                      y_label=choicealias,y_label_visible=False)
        else:
            P= [P_main]
        return P
    


        

