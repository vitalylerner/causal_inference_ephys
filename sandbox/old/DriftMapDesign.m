f=gcf;
Lines=findobj(gcf,'Type','Scatter');
for iLine=1:numel(Lines)
    l=Lines(iLine);
    x=get(l,'Xdata');
    y=get(l,'Ydata');
    hold on
    a=0.8;
    l2=scatter(x,y,.5,'o','markerfacecolor',[0.2 0.2 0.2],'markeredgecolor',[0.2 0.2 0.2],'markerfacealpha',a,'markeredgealpha',a);
    alpha(l2,a)
    set(l,'visible','off')
    
    %set(l,'Color',[0.5 0.5 0.5],'Marker','.','MarkerSize',0.1,'markerAlpha',0.1)
    %#l.MarkerFaceAlpha=.2;
    %,'Alpha',0.1)
    %hold off
    %alpha(0.01)
end