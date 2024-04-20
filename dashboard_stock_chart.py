# -*- coding: utf-8 -*-
"""
Created on Fri Mar 10 10:23:54 2023

@author: IKU-Trader
"""

import numpy as np
import pandas as pd
from datetime import datetime

import dash
import dash_bootstrap_components as dbc
from dash import Dash, dcc, html, dash_table
from dash.dependencies import Input, Output, State

import plotly
import plotly.graph_objs as go

from plotly.figure_factory import create_candlestick
from YahooFinanceApi import YahooFinanceApi

from TimeUtils import TimeUtils


TICKERS = ['^DJI', 'CS', 'MS', 'AAPL', 'AMZN', 'META']
TIMEFRAMES = list(YahooFinanceApi.TIMEFRAMES.keys())
BARSIZE = ['50', '100', '150', '200', '300', '400']

INTERVAL_MSEC = 10000

app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

# ----
setting_bar = dbc.Row([
                        html.H5('Settings',
                        style={'margin-top': '2px', 'margin-left': '24px'})
                        ],
                        style={"height": "3vh"},
                        className='bg-primary text-white')

ticker_dropdown = dcc.Dropdown(id='symbol_dropdown',
                             multi=False,
                             value=TICKERS[0],
                             options=[{'label': x, 'value': x} for x in TICKERS],
                             style={'width': '140px'})

ticker = html.Div([ html.P('Ticker Symbol',
                           style={'margin-top': '8px', 'margin-bottom': '4px'}, 
                           className='font-weight-bold'),
                   ticker_dropdown])
 
timeframe_dropdown = dcc.Dropdown(id='timeframe_dropdown', 
                                  multi=False, 
                                  value=TIMEFRAMES[1], 
                                  options=[{'label': x, 'value': x} for x in TIMEFRAMES],
                                  style={'width': '120px'})                
timeframe =  html.Div([
                                html.P('Time Frame',
                                       style={'margin-top': '16px', 'margin-bottom': '4px'},
                                       className='font-weight-bold'),
                                timeframe_dropdown])

barsize_dropdown = dcc.Dropdown(id='barsize_dropdown', 
                                multi=False, 
                                value=BARSIZE[2],
                                options=[{'label': x, 'value': x} for x in BARSIZE],
                                style={'width': '120px'})

barsize = html.Div([    html.P('Display Bar Size',
                               style={'margin-top': '16px', 'margin-bottom': '4px'},
                               className='font-weight-bold'),
                        barsize_dropdown])

sidebar =  html.Div([
                        setting_bar,
                        html.Div([ticker,
                                 timeframe,
                                 barsize,
                                 html.Hr()],
                        style={'height': '50vh', 'margin': '8px'})
                    ])
    
contents = html.Div([    
                        dbc.Row([
                                    html.H5('YahooFinance', style={'margin-top': '2px', 'margin-left': '24px'})
                                ],
                                style={"height": "3vh"}, className='bg-primary text-white'),
                        dbc.Row([
                                    html.Div(id='chart_output'),
                                ],
                                style={"height": "40vh"}, className='bg-white'),
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
                                        dbc.Col(sidebar, width=2, className='bg-light'),
                                        dbc.Col(contents, width=9)
                                    ],
                                    style={"height": "100vh"}),
                            ],
                            fluid=True)
@app.callback(
    Output('chart_output', 'children'),
    Input('timer', 'n_intervals'),
    State('symbol_dropdown', 'value'), State('timeframe_dropdown', 'value'), State('barsize_dropdown', 'value')
)
def updateChart(interval, symbol, timeframe, num_bars):
    num_bars = int(num_bars)
    #print(symbol, timeframe, num_bars)
    df = YahooFinanceApi.download(symbol, timeframe, TimeUtils.TIMEZONE_TOKYO)
    if len(df) > num_bars:
        df = df.iloc[-num_bars:, :]
    return createChart(symbol, timeframe, df)
  
def createChart(symbol, timeframe, df):
    fig = create_candlestick(df['open'], df['high'], df['low'], df['close'])
    time = df.index
    #print(symbol, timeframe, dic)
    xtick = (5 - time[0].weekday()) % 5
    tfrom = time[0].strftime('%Y-%m-%d %H:%M')
    tto = time[-1].strftime('%Y-%m-%d %H:%M')
    if timeframe == 'D1' or timeframe == 'H1':
        form = '%m-%d'
    else:
        form = '%d/%H:%M'
    fig['layout'].update({
                            'title': symbol + '  ' + timeframe + '  ('  +  tfrom + ')  ...  (' + tto + ')',
                            'xaxis':{
                                        'title': 'Time',
                                        'showgrid': True,
                                        'ticktext': [x.strftime(form) for x in time][xtick::5],
                                        'tickvals': np.arange(xtick, len(time), 5)
                                    },
                            'yaxis':{
                                        'title': 'Price'
                                    }
       })
    #print(fig)
    return dcc.Graph(id='stock-graph', figure=fig)

if __name__ == '__main__':
    app.run_server(debug=True, port=3333)



