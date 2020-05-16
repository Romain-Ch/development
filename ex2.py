#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 12 15:48:34 2020

@author: romain
"""

import pandas as pd

df = pd.read_csv('/Users/romain/Documents/kaggle/COVID-19-geographic-disbtribution-worldwide.csv',
                 sep = ';',
                 parse_dates = True)

df.info()
df.isnull().sum()

df.isnull().sum()

df.shape
df.head()
df.describe()


freq1 = df.groupby('countriesAndTerritories')['cases', 'deaths'].sum().sort_values(by = 'cases', ascending = False).reset_index().rename(columns={"index": "x"})
df_france = df[(df['countriesAndTerritories'] == 'France')]


import plotly.graph_objects as go
import plotly.figure_factory as ff

from plotly.subplots import make_subplots

from plotly.offline import plot



colors = ['lightslategray',] * 10
colors[7] = 'crimson'

fig = make_subplots(rows = 2, cols = 1,
                    specs=[[{"type": "bar"}],
                           [{"type": "scatter"}]])

fig.add_trace(
    go.Bar(x=freq1['countriesAndTerritories'][0:10], y=freq1['cases'][0:10],
           name = 'top 10 of covid 19 cases',
           marker_color =  colors),
    row = 1, col = 1)

# line plot
fig.add_trace(
    go.Scatter(x = df_france['dateRep'], y = df_france['deaths'],
               mode = 'lines',
               name = 'deaths in France',
               marker_color = 'crimson'),
    row = 2, col = 1)


# formatting x ticks
fig.update_layout(
    xaxis_tickformat = '%d %B (%a)<br>%Y'
)

fig.show()
plot(fig)