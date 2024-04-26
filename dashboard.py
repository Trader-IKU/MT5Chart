# -*- coding: utf-8 -*-
"""
Created on Fri Mar 10 10:23:54 2023

@author: IKU-Trader
"""

import os
import shutil
import sys
sys.path.append('../Libraries/trade')

import numpy as np
import pandas as pd
from datetime import datetime, date
import time

import dash
import dash_bootstrap_components as dbc
from dash import Dash, dcc, html, dash_table
from dash.dependencies import Input, Output, State

import plotly
import plotly.graph_objs as go
from plotly.figure_factory import create_candlestick

from ta.trend import MACD
from ta.momentum import StochasticOscillator
from technical import VWAP, BB, ATR_TRAIL

from utils import Utils
from mt5_api import Mt5Api

TICKERS = ['NIKKEI', 'DOW', 'NSDQ', 'USDJPY']
TIMEFRAMES = ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1']
BARSIZE = ['100', '200', '400', '600', '800', '1500', '2000']
HOURS = list(range(0, 24))
MINUTES = list(range(0, 60))

INTERVAL_MSEC = 30 * 1000

technical_param1 = {'bb_window':30, 'bb_ma_window':80, 'bb_multiply': 1.8, 'vwap_multiply': 1.8, 'vwap_begin_hour': 7}
technical_param2 = {'atr_window': 50, 'atr_multiply': 2.0, 'peak_hold_term': 10}


api = Mt5Api()
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

# ----


    
def select_symbol(number: int):
    number = str(number)   
    header = dbc.Row([
                    html.H5('Chart' + number ,
                    style={'margin-top': '2px', 'margin-left': '24px'})
                    ],
                    style={"height": "3vh"},
                    className='bg-primary text-white')                        
    
    symbol_dropdown = dcc.Dropdown(id='symbol_dropdown' + number,
                             multi=False,
                             value=TICKERS[0],
                             options=[{'label': x, 'value': x} for x in TICKERS],
                             style={'width': '140px'})

    symbol = html.Div([ html.P('Ticker Symbol',
                           style={'margin-top': '8px', 'margin-bottom': '4px'}, 
                           className='font-weight-bold'),
                           symbol_dropdown])
 
    timeframe_dropdown = dcc.Dropdown(id='timeframe_dropdown' + number, 
                                  multi=False, 
                                  value=TIMEFRAMES[0], 
                                  options=[{'label': x, 'value': x} for x in TIMEFRAMES],
                                  style={'width': '120px'})                
    timeframe =  html.Div([
                                html.P('Time Frame',
                                       style={'margin-top': '16px', 'margin-bottom': '4px'},
                                       className='font-weight-bold'),
                                        timeframe_dropdown])

    barsize_dropdown = dcc.Dropdown(id='barsize_dropdown' + number, 
                                multi=False, 
                                value=BARSIZE[2],
                                options=[{'label': x, 'value': x} for x in BARSIZE],
                                style={'width': '120px'})

    barsize = html.Div([    html.P('Display Bar Size',
                               style={'margin-top': '16px', 'margin-bottom': '4px'},
                               className='font-weight-bold'),
                                barsize_dropdown])
    return [header, symbol, timeframe, barsize] 

vwap_multiply = dcc.Input(id='vwap_multiply',type="number", min=1.0, max=4.0, step=0.1, value=1.8)
vwap_begin_hour = dcc.Input(id='vwap_begin_hour',type="number", min=0, max=23, step=1, value=7)
bb_window = dcc.Input(id='bb_window',type="number", min=10, max=100, step=1, value=30)
bb_ma_window = dcc.Input(id='bb_ma_window',type="number", min=10, max=100, step=1, value=80)
bb_multiply = dcc.Input(id='bb_multiply',type="number", min=1.0, max=4.0, step=0.1, value=1.8)

params1 = html.Div([html.P('VWAP Begin Hour'), vwap_begin_hour])
params2 = html.Div([html.P('VWAP Multiply'), vwap_multiply])
params3 = html.Div([html.P('BB Window'), bb_window])
params4 = html.Div([html.P('Bb MA Window'), bb_ma_window])
params5 = html.Div([html.P('BB Multiply'), bb_multiply])

symbol1 = select_symbol(1)
sidebar1 =  html.Div([
                        symbol1[0],
                        html.Div([
                                    symbol1[1],
                                    symbol1[2],
                                    symbol1[3],
                                    html.Hr(),
                                    params1,
                                    params2,
                                    params3,
                                    params4,
                                    params5,
                                    html.Hr()],
                                style={'height': '50vh', 'margin': '8px'})
                    ])
 


atr_window = dcc.Input(id='atr_window',type="number", min=10, max=100, step=10, value=technical_param2['atr_window'])
atr_multiply = dcc.Input(id='atr_multiply',type="number", min=1, max=4, step=0.1, value=technical_param2['atr_multiply'])
peak_hold_term = dcc.Input(id='peak_hold_term',type="number", min=10, max=100, step=1, value=technical_param2['peak_hold_term'])

param6 = html.Div([html.P('ATR window'), atr_window])
param7 = html.Div([html.P('ATR Multiply'), atr_multiply])
param8 = html.Div([html.P('Peakhold'), peak_hold_term]) 
symbol2 = select_symbol(2)
sidebar2 =  html.Div([
                        symbol2[0],
                        html.Div([
                                    symbol2[1],
                                    symbol2[2],
                                    symbol2[3],
                                    html.Hr(),
                                    param6,
                                    param7,
                                    param8,
                                    html.Hr()],
                                style={'height': '50vh', 'margin': '8px'})
                    ])
    
contents = html.Div([    
                        dbc.Row([
                                    html.H5('MetaTrader', style={'margin-top': '2px', 'margin-left': '24px'})
                                ],
                                style={"height": "3vh"}, className='bg-primary text-white'),
                        dbc.Row([
                                    html.Div(id='chart'),
                                ],
                                style={"height": "400vh"}, className='bg-white'),
                        dbc.Row([
                                    html.Div(id='table_container')
                                ],
                                #style={"height": "20vh"}, className='bg-primary text-white'
                                ),
                        dcc.Interval(
                                        id='timer',
                                        interval=INTERVAL_MSEC,
                                        n_intervals=0)
                    ])

app.layout = dbc.Container([
                            dbc.Row(
                                    [
                                        dbc.Col(sidebar1, width=1, className='bg-light'),
                                        dbc.Col(sidebar2, width=1, className='bg-light'),
                                        dbc.Col(contents, width=9)
                                    ],
                                    style={"height": "150vh"}),
                            ],
                            fluid=True)

# -----

@app.callback(
    Output('chart', 'children'),
    Input('timer', 'n_intervals'),
    
    State('symbol_dropdown1', 'value'), 
    State('timeframe_dropdown1', 'value'), 
    State('barsize_dropdown1', 'value'),
    State('vwap_begin_hour', 'value'), 
    State('vwap_multiply', 'value'),
    State('bb_window', 'value'), 
    State('bb_ma_window', 'value'),
    State('bb_multiply', 'value'),
    
    State('symbol_dropdown2', 'value'), 
    State('timeframe_dropdown2', 'value'), 
    State('barsize_dropdown2', 'value'),
    State('atr_window', 'value'), 
    State('atr_multiply', 'value'), 
    State('peak_hold_term', 'value')
)
def update_chart(interval,
                 symbol1,
                 timeframe1,
                 num_bars1,
                 vwap_begin_hour,
                 vwap_multiply,
                 bb_window,
                 bb_ma_window, 
                 bb_multiply,
                 symbol2,
                 timeframe2,
                 num_bars2,
                 atr_window,
                 atr_multiply,
                 peak_hold_term
                 ):
    technical_param1['vwap_begin_hour'] = vwap_begin_hour
    technical_param1['vwap_multiply'] = vwap_multiply
    technical_param1['bb_window'] = bb_window
    technical_param1['bb_ma_window'] = bb_ma_window
    technical_param1['bb_multiply'] == bb_multiply
    
    num_bars1 = int(num_bars1)
    data1 = api.get_rates(symbol1, timeframe1, num_bars1 + 60 * 24)
    fig1 = create_chart1(data1, num_bars1)

    technical_param2['atr_window'] = atr_window
    technical_param2['atr_multiply'] = atr_multiply
    technical_param2['peak_hold_term'] = peak_hold_term
    
    num_bars2 = int(num_bars2)
    data2 = api.get_rates(symbol2, timeframe2, num_bars2 + 60 * 24)
    fig2 = create_chart2(data2, num_bars2)
    return create_graph(symbol1, timeframe1, fig1, data1), create_graph(symbol2, timeframe2, fig2, data2)


def indicators1(data, param):
    vwap_begin_hour = param['vwap_begin_hour']
    VWAP(data, param['vwap_multiply'], begin_hour=vwap_begin_hour)
    # ATR(self.data, 15, 100)
    BB(data, param['bb_window'], param['bb_ma_window'], param['bb_multiply'])      

def create_chart1(data, num_bars):
    t0 = time.time()
    indicators1(data, technical_param1)
    data = Utils.sliceDictLast(data, num_bars)
    jst = data['jst']
    n = len(jst)
    print('Elapsed Time:', time.time() - t0)
    #print(time[:5])
    # Declare plotly figure (go)
    fig=go.Figure()

    # add subplot properties when initializing fig variable
    fig = plotly.subplots.make_subplots(rows=4, cols=1, shared_xaxes=True,
                    vertical_spacing=0.01, 
                    row_heights=[0.5,0.1,0.2,0.2])

    fig.add_trace(go.Candlestick(x=jst,
                    open=data['open'],
                    high=data['high'],
                    low=data['low'],
                    close=data['close'], name = 'market data'))
    
    fig.add_trace(go.Scatter(x=jst, 
                         y=data['VWAP_UPPER'], 
                         opacity=0.7, 
                         line=dict(color='blue', width=2), 
                         name='VWAP Upper'))

    fig.add_trace(go.Scatter(x=jst, 
                         y=data['VWAP_LOWER'], 
                         opacity=0.7, 
                         line=dict(color='orange', width=2), 
                         name='VWAP lower'))

    # Plot volume trace on 2nd row
    
    colors = ['green' if data['open'][i] - data['close'][i] >= 0 
          else 'red' for i in range(n)]
    fig.add_trace(go.Bar(x=jst, 
                     y=data['tick_volume'],
                     marker_color=colors
                    ), row=2, col=1)

    #print(data['VWAP_CROSS_UP'][100: ])

    fig.add_trace(go.Scatter(x=jst,
                         y=data['VWAP_UP'],
                         line=dict(color='blue', width=2)
                        ), row=3, col=1)
    
    fig.add_trace(go.Scatter(x=jst,
                        y=data['VWAP_DOWN'],
                        line=dict(color='red', width=2)
                    ), row=3, col=1)

    # Plot stochastics trace on 4th row
    fig.add_trace(go.Scatter(x=jst,
                         y=data['BB_UP'],
                         line=dict(color='blue', width=2)
                        ), row=4, col=1)
    
    fig.add_trace(go.Scatter(x=jst,
                         y=data['BB_DOWN'],
                         line=dict(color='red', width=2)
                        ), row=4, col=1)
    
    # update y-axis label
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="VWAP Band", showgrid=False, row=3, col=1)
    fig.update_yaxes(title_text="BB Band", row=4, col=1)     
    return fig


def create_chart2(data, num_bars):
    t0 = time.time()
    ATR_TRAIL(data, technical_param2['atr_window'], technical_param2['atr_multiply'], technical_param2['peak_hold_term'])
    data = Utils.sliceDictLast(data, num_bars)
    jst = data['jst']
    n = len(jst)
    print('Elapsed Time2:', time.time() - t0)
    #print(time[:5])
    # Declare plotly figure (go)
    fig=go.Figure()

    # add subplot properties when initializing fig variable
    fig = plotly.subplots.make_subplots(rows=4, cols=1, shared_xaxes=True,
                    vertical_spacing=0.01, 
                    row_heights=[0.5,0.1,0.2,0.2])

    fig.add_trace(go.Candlestick(x=jst,
                    open=data['open'],
                    high=data['high'],
                    low=data['low'],
                    close=data['close'], name = 'market data'))
    
    fig.add_trace(go.Scatter(x=jst, 
                         y=data['ATR_TRAIL_UP'], 
                         opacity=0.7, 
                         line=dict(color='blue', width=2), 
                         name='ATR Trail Up'))

    fig.add_trace(go.Scatter(x=jst, 
                         y=data['ATR_TRAIL_DOWN'], 
                         opacity=0.7, 
                         line=dict(color='orange', width=2), 
                         name='ATR Trail down'))
    
    colors = ['green' if data['open'][i] - data['close'][i] >= 0 else 'red' for i in range(n)]
    fig.add_trace(go.Bar(x=jst, 
                     y=data['tick_volume'],
                     marker_color=colors
                    ), row=2, col=1)
    
    # update y-axis label
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)  
    return fig

def create_graph(symbol, timeframe, fig, data):
    jst = data['jst']
    #print(symbol, timeframe, time[:10])
    #print(df.columns)
    xtick = (5 - jst[0].weekday()) % 5
    tfrom = jst[0]
    tto = jst[-1]
    if timeframe == 'D1' or timeframe == 'H1':
        form = '%m-%d'
    else:
        form = '%d/%H:%M'
    # update layout by changing the plot size, hiding legends & rangeslider, and removing gaps between dates
    fig.update_layout(height=900, width=1100, 
                    showlegend=False, 
                    xaxis_rangeslider_visible=False)
                    

    # Make the title dynamic to reflect whichever stock we are analyzing
    fig.update_layout(
        title= symbol + '(' + timeframe + ') ' + 'Live Share Price:',
        yaxis_title='Stock Price') 

      

    fig['layout'].update({
                            'title': symbol + '  ' + timeframe + '  ('  +  str(tfrom) + ')  ...  (' + str(tto) + ')',
                            'xaxis':{
                                        'title': 'Time',
                                        'showgrid': True,
                                        'ticktext': [x.strftime(form) for x in jst][xtick::5],
                                        'tickvals': np.arange(xtick, len(jst), 5)
                                    }
                        })
                            
    return dcc.Graph(id='stock-graph', figure=fig)

if __name__ == '__main__':
    app.run_server(debug=True, port=3333)



