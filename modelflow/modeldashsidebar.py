# -*- coding: utf-8 -*-
"""
Created on Fri May 14 22:46:21 2021

@author: bruger
"""

import dash
from jupyter_dash import JupyterDash
from jupyter_dash.comms import _send_jupyter_config_comm_request
from dash import dcc 

import dash_bootstrap_components as dbc
from dash import html
from dash.dependencies import Input, Output, State
from  dash_interactive_graphviz import DashInteractiveGraphviz
import plotly.graph_objs as go
from plotly.graph_objs.scatter.marker import Line

import webbrowser
from threading import Timer

import json
import networkx as nx


from pathlib import Path
import pandas as pd

from modelhelp import cutout

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


initial_dot_source = """
digraph  {
node[style="filled"]
a ->b->d
a->c->d
}
"""

sidebar_width, adbar_width = "16rem", "12rem"
# the style arguments for the sidebar. We use position:fixed and a fixed width
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": sidebar_width,
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
    "overflow": "scroll",
}

# the styles for the main content position it to the right of the sidebar and
# add some padding.
CONTENT_STYLE_TOP = {
    "background-color": "f8f9fa",
    "margin-left": sidebar_width,
}
CONTENT_STYLE_GRAPH = {
    "background-color": "f8f9fa",
    "margin-left": sidebar_width,"overflow": "scroll",
}
CONTENT_STYLE_TAB = {
    "background-color": "f8f9fa",
    "margin-left": sidebar_width,
}


def app_setup(jupyter=False):  
    if jupyter: 
        # Timer(1,_send_jupyter_config_comm_request).start()
        # JupyterDash.infer_jupyter_proxy_config()
        app = JupyterDash(__name__,external_stylesheets=[dbc.themes.BOOTSTRAP])
    else:
        app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    return app                 

def app_run(app,jupyter=False,debug=False,port=5000,inline=True):
    def open_browser(port=port):
    	webbrowser.open_new(f"http://localhost:{port}")
    
       
    if jupyter:
        if inline:
            app.run_server(debug=debug,port=port,mode='inline')
        else:     
            Timer(1, open_browser).start()            
            app.run_server(debug=debug,port=port,mode='external')

    else:    
        Timer(1, open_browser).start()            

        app.run_server(debug=debug,port=port)


def get_stack(df,v='Guess it',heading='Yes',pct=True,threshold=0.5):
    pv = cutout(df,threshold)
    template =  '%{y:10.0f}%' if pct else '%{y:15.2f}' 
    trace = [go.Bar(x=pv.columns.astype('str'), y=pv.loc[rowname,:], name=rowname,hovertemplate = template,) for rowname in pv.index]
    out = { 'data': trace,
    'layout':
    go.Layout(title=f'{heading}', barmode='relative',legend_itemclick='toggleothers',
              yaxis = {'tickformat': ',.0','ticksuffix':'%' if pct else ''})
    }
    return out 

def get_line_old(pv,v='Guess it',heading='Yes'):
    trace = [go.Line(x=pv.columns.astype('str'), y=pv.loc[rowname,:], name=rowname) for rowname in pv.index]
    out = { 'data': trace,
    'layout':
    go.Layout(title=f'{heading}')
    }
    return out 
def get_line(pv,v='Guess it',heading='Yes'):
    trace = [go.Scatter(x=pv.columns.astype('str'),
                  y=pv.loc[rowname,:], 
                  name=rowname
                  ) for rowname in pv.index]
    out = { 'data': trace,
    'layout':
    go.Layout(title=f'{heading}')
    }
    return out 


def generate_table(dataframe, max_rows=10):
    return html.Table([
        html.Thead(
            html.Tr([html.Th('var')]+[html.Th(col) for col in dataframe.columns])
        ),
        html.Tbody([
            html.Tr([html.Td(dataframe.index[i])]+[html.Td(f'{dataframe.iloc[i][col]:25.2f}') for col in dataframe.columns]) 
            for i in range(min(len(dataframe), max_rows))
        ])
    ])




class Dash_Mixin():
    
          
    def modeldash(self,pre_var='FY',debug=False,jupyter=False,show_trigger=False,port=5001,lag= False,filter = 0,up=1,down=0,
                  threshold=0.5,inline=True): 
        print('Still worlking on the layout of this')
        self.dashport = port
        selected_var = pre_var if pre_var else sorted(self.allvar.keys())[0] 
        sidebar = html.Div(
            [ 
              html.H3("Current Variable"),
              dcc.Markdown(
                  id='outvar_state',
                  children=f'{selected_var}'),
              
              html.H3("Select a variable"),             
              dcc.Dropdown(id='var',value=selected_var,options=[
                  dict(label=v, value=v)
                  for v in sorted(self.allvar.keys())]),
             
              html.H3("Up Levels"),
              dcc.Dropdown(id="up",value=up,options=[
                  dict(label=engine, value=engine)
                  for engine in list(range(10))]),

              html.H3("Down levels"),
              dcc.Dropdown(id="down",value=down,options=[
                  dict(label=engine, value=engine)
                  for engine in list(range(10))]),
             
               html.H3("Graph Show"),             
               dcc.RadioItems(id='graph_show',
               options=[
                   {'label': 'Variables', 'value': 'v'},
                   {'label': 'Attributions', 'value': 'a'},
                   ],
                   value='a',labelStyle={'display': 'block'}),
             
            
              html.H3("Plot show"),             
              dcc.RadioItems(id='plot_show',
              options=[
                  {'label': 'Values', 'value': 'Values'},
                  {'label': 'Diff', 'value': 'Diff'},
                  {'label': 'Attributions pct.', 'value': 'Att'},
                  {'label': 'Attributions level', 'value':  'Attlevel'},
                  ],
              value='Values',labelStyle={'display': 'block'}),  
             
              html.H3("Graph orientation"),             
              dcc.RadioItems(id='orient',
              options=[
                  {'label': 'Vertical', 'value':'v'},
                  
                  {'label': 'Horisontal', 'value': 'h'},
                  ],
            value='v',labelStyle={'display': 'block'}),
              
              html.H3("Behavior when clicking on graph"),             
              dcc.RadioItems(id='onclick',
              options=[
                  {'label': 'Center when click', 'value':'c'},                  
                  {'label': 'Display when click', 'value': 'd'},
                  ],
            value='c',labelStyle={'display': 'block'}),
                   
             
            ],
            style=SIDEBAR_STYLE
        )
        # top =   dbc.Col([
        #                 dcc.Graph(
        #                 id='plot',
        #                 figure=get_line(self.value_dic[selected_var].iloc[:2,:],selected_var,f'The values for {selected_var}'))
        #                  ],
        #                     width={'size':12,'offset':1,'order':'last'},
        #                     style=CONTENT_STYLE_TOP)
        
        # graph = dbc.Col( DashInteractiveGraphviz(id="gv" , style=CONTENT_STYLE_GRAPH, 
        #                 dot_source =   self.draw(selected_var,up=up,down=down,showatt=False,lag=lag,
        #                                          debug=0,dot=True,HR=False,filter = filter))
                                     
        #                  ,width={'size':12,'offset':1,'order':'last'},
        #                  style=CONTENT_STYLE_GRAPH)
        
        
        
        # twopanel = ([
        #     dbc.Row(top ,className="h-50",justify='start' ),
        #     dbc.Row(graph,className="h-50",justify='start')])
        
        # onepanel = [
        #     dbc.Row(graph,className="h-100",justify='start')]
        
        # body2 = dbc.Container(twopanel,id='body2',style={"height": "100vh"},fluid=True)
        # body1 = dbc.Container(onepanel,id='body',style={"height": "100vh"},fluid=True)
        
        tab0 = html.Div([
            dcc.Tabs(id="tabs", value='tab-graph', children=[
                dcc.Tab(label='Graph', value='tab-1-example-graph'
                        ,children= [DashInteractiveGraphviz(id="gv" , style=CONTENT_STYLE_GRAPH, 
                        dot_source =   self.draw(selected_var,up=up,down=down,showatt=False,lag=lag,
                                                 debug=0,dot=True,HR=False,filter = filter))],
                        style=CONTENT_STYLE_TOP),

                dcc.Tab(label='Chart', value='tab-att',
                        children = [dcc.Graph(id='plot',
                        figure=get_line(self.value_dic[selected_var].iloc[:2,:],selected_var,f'The values for {selected_var}'))
                         ],                            
                        style=CONTENT_STYLE_TOP)

                    ]),
                  ],style = CONTENT_STYLE_TAB)
        # tabbed = tab0
        tabbed = dbc.Container(tab0,id='tabbed',style={"height": "100vh"},fluid=True)
        app  = app_setup(jupyter=jupyter)
    
        
        
        # app.layout = html.Div([sidebar,body2])
        app.layout = dbc.Container([sidebar,tabbed],style={"height": "100vh"},fluid=True)

        @app.callback(
            [Output("gv", "dot_source"),Output('plot','figure'), Output('outvar_state','children')],
            [Input('var', "value"),
                Input('gv', "selected_node"),Input('gv', "selected_edge"),
                  Input('up', "value"),Input('down', "value"),
                  Input('graph_show', "value"),
                   Input('plot_show', "value"),
                  Input('orient', "value"),
                  Input('onclick','value')

               ]
               , State('outvar_state','children')
        )
        def display_output( var,
                            selected_node,selected_edge,
                              up,down,
                              graph_show,
                                plot_show,
                               orient,
                               onclick,
                             outvar_state
                            ):
            ctx = dash.callback_context
            if ctx.triggered:
                trigger = ctx.triggered[0]['prop_id'].split('.')[0]
                if show_trigger:
                    ctx_msg = json.dumps({
                    'states': ctx.states,
                    'triggered': ctx.triggered,
                    'inputs': ctx.inputs
                          }, indent=2)
                    print(ctx_msg)
                    # print(f'{outvar=},{data_show=}')
                    # print(value)
                              
                if trigger in ['var']:
                    try:
                        outvar=var[:]
                    except:
                        return [dash.no_update,dash.no_update,dash.no_update]
                    

              
                elif trigger == 'gv':
                    pass
                    try:
                        xvar= selected_node.split('(')[0]
                        if xvar in self.endogene or xvar in self.exogene: 
                            outvar = xvar[:]
                    except:
                        outvar = selected_edge.split('->')[0]
                else:
                    ...
                    
                    outvar=outvar_state
                      
                if onclick == 'c' or outvar not in self.value_dic.keys() or trigger == 'orient' :   
                    dot_out =  self.draw(outvar,up=up,down=down,filter=filter,showatt=False,debug=0,
                                         lag=lag,dot=True,HR=orient=='h')
                else:
                    dot_out = dash.no_update
                      
                if plot_show == 'Values':
                    plot_out = get_line(self.value_dic[outvar].iloc[:2,:],outvar,f'The values for {outvar}')
                elif plot_show == 'Diff':
                    plot_out = get_line(self.value_dic[outvar].iloc[[2],:],outvar,f'The impact for {outvar}')
                elif plot_show == 'Att':
                   if outvar in self.endogene:         
                       plot_out = get_stack(self.att_dic[outvar],outvar,f'Attribution of the impact - pct. for {outvar}',threshold=threshold)
                   else: 
                       plot_out = get_line(self.value_dic[outvar].iloc[:2,:],outvar,outvar)
                elif plot_show == 'Attlevel':
                   if outvar in self.endogene:         
                       plot_out = get_stack(self.att_dic_level[outvar],outvar,f'Attribution of the impact - level for {outvar}',pct=False,threshold=threshold)
                   else: 
                       plot_out = get_line(self.value_dic[outvar].iloc[:2,:],outvar,outvar)
                else:
                    # breakpoint()
                    plot_out = get_line(self.value_dic[outvar].iloc[[2],:],outvar,outvar)
                 
            else:
                return [dash.no_update,dash.no_update,dash.no_update]

                
            return [dot_out,plot_out,outvar]
       
        app_run(app,jupyter=jupyter,debug=debug,port=self.dashport,inline=inline)
#%% test        
if __name__ == "__main__":
    from modelclass import model 

        
    if not  'baseline' in locals():    
        madam,baseline  = model.modelload('../Examples/ADAM/baseline.pcim',run=1,silent=0 )
        # make a simpel experimet VAT
        scenarie = baseline.copy()
        scenarie.TG = scenarie.TG + 0.05
        _ = madam(scenarie)
        
   
    setattr(model, "modeldash", Dash_Mixin.modeldash)    
    madam.modeldash('FY',jupyter=False,show_trigger=False,debug=False) 
    #mmodel.FY.draw(up=1, down=1,svg=1,browser=1)

