#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np

from datetime import date, timedelta
from time import strftime, gmtime

import plotly.graph_objects as go

from plotly.subplots import make_subplots
from plotly.offline import plot

# import COVID-19 world data
df_covid_monde = pd.read_csv(
    'https://opendata.ecdc.europa.eu/' 'covid19/casedistribution/csv',
    sep=',',
    parse_dates=True,
)

df_covid_monde.info()
df_covid_monde.isnull().sum()

today = date.today() - timedelta(2)
date_of_today = (
    today.strftime('%Y-%m-%d') + '-' + strftime('%Hh%M', gmtime(60 * 60 * 19))
)

uri = (
    f'https://static.data.gouv.fr/resources/'
    f'donnees-hospitalieres-relatives-a-lepidemie-de-covid-19/'
    f'20200516-190022/donnees-hospitalieres-etablissements-covid19-'
    f'{date_of_today}'
    f'.csv'
)

# import COVID-19 french data
df_covid_det_france = pd.read_csv(uri, sep=';', parse_dates=True)

df_covid_det_france.isnull().sum()
df_covid_det_france.info()
df_covid_det_france.shape

freq_covid_monde = (
    df_covid_monde.groupby(['countriesAndTerritories', 'continentExp'])[
        ['cases', 'deaths']
    ]
    .sum()
    .sort_values(by='cases', ascending=False)[0:10]
    .reset_index()
    .rename(columns={"index": "x"})
)

df_covid_france = df_covid_monde[
    (df_covid_monde['countriesAndTerritories'] == 'France')
]

freq_covid_france = (
    df_covid_france.groupby(['dateRep', 'month'])[['cases', 'deaths']]
    .sum()
    .sort_values(by='cases', ascending=False)[0:15]
    .reset_index()
    .rename(columns={'index': 'x'})
)

df_covid_france = df_covid_france[['dateRep', 'month', 'deaths']]

freq_covid_france_dep = (
    df_covid_det_france.groupby('dep')['nb']
    .sum()
    .sort_values(ascending=False)[0:10]
    .reset_index()
    .rename(columns={'index': 'x'})
)

# pie_values = freq_covid_france_dep.values.tolist()
pie_values = freq_covid_france_dep['nb'].tolist()
pie_labels = freq_covid_france_dep['dep'].tolist()

list_of_countries = freq_covid_monde['countriesAndTerritories'].values.tolist()

list_of_dep = freq_covid_france_dep.index.tolist()

freq_covid_monde['obs'] = np.arange(len(freq_covid_monde))

# make a subplot
fig = make_subplots(
    rows=2,
    cols=2,
    specs=[
        [{'secondary_y': True, 'type': 'xy'}, {'secondary_y': True, 'type': 'xy'}],
        [{'type': 'pie'}, {'type': 'domain'}],
    ],
    subplot_titles=[
        'Top 10 of coutries the most infected',
        'French deaths per day',
        ' ',
        'French deaths per department',
    ],
)


# 1st chart : add a bar chart
fig.add_trace(
    go.Scatter(
        x=freq_covid_monde['countriesAndTerritories'],
        y=freq_covid_monde['cases'],
        mode='markers+lines',
        name='World cases',
        marker_color='black',
    ),
    row=1,
    col=1,
    secondary_y=True,
)

nb_pays = len(freq_covid_monde['countriesAndTerritories'])
type(nb_pays)
colors = ['cornflowerblue',] * nb_pays

list_pos_France = freq_covid_monde[
    freq_covid_monde['countriesAndTerritories'] == 'France'
].index.tolist()
pos_France = int(str(list_pos_France).strip('[]'))


if pos_France > 0:
    colors[pos_France] = 'crimson'

# 1st chart : add a plot line on the secondary axe
fig.add_trace(
    go.Bar(
        x=freq_covid_monde['countriesAndTerritories'],
        y=freq_covid_monde['deaths'],
        name='World deaths',
        marker_color=colors,
    ),
    row=1,
    col=1,
    secondary_y=False,
)

# Add 2nd Chart : bar chart
fig.add_trace(
    go.Bar(
        x=freq_covid_france['dateRep'],
        y=freq_covid_france['deaths'],
        name='French deaths',
        marker_color='crimson',
    ),
    row=1,
    col=2,
    secondary_y=False,
)
#
# fig.add_trace(
#     go.Bar(
#         x=freq_covid_france['dateRep'],
#         y=freq_covid_france['cases'],
#         name='French cases',
#         marker_color='lightsalmon',
#     ),
#     row=1,
#     col=2,
# )


# add pie chart
fig.add_trace(
    go.Pie(
        labels=pie_labels,
        values=pie_values,
        hole=0.4,
        textinfo='label+percent',
        textposition='inside',
    ),
    row=2,
    col=2,
)

fig.show()
plot(fig)

# Add drowdowns
button_layer_1_height = 1.35

# Add figure title
fig.update_layout(
    title={
        'text': "COVID-19 Situation",
        'y': 0.85,
        'x': 0.5,
        'xanchor': 'center',
        'yanchor': 'top',
    },
    # barmode='group',
    showlegend=False,
    updatemenus=list(
        [
            dict(
                type='dropdown',
                direction='down',
                x=0.04,
                y=button_layer_1_height,
                showactive=True,
                pad={"r": 10, "t": 10},
                font={'size': 10},
                xanchor='left',
                yanchor='top',
                buttons=list(
                    [
                        dict(
                            method='update',
                            args=[{'visible': visibility}],
                            label='America',
                        ),
                        dict(
                            method='update',
                            args=[
                                {
                                    'y': [
                                        freq_covid_monde['cases'],
                                        freq_covid_monde['deaths'],
                                    ],
                                    'x': [freq_covid_monde['countriesAndTerritories']],
                                    'type': 'bar',
                                },
                                [[1], [2], [3], [4], [6], [8]],
                            ],
                            label='Europe',
                        ),
                        dict(
                            method='update',
                            args=[
                                {
                                    'y': [
                                        freq_covid_monde['cases'],
                                        freq_covid_monde['deaths'],
                                    ],
                                    'x': [freq_covid_monde['countriesAndTerritories']],
                                    'type': 'bar',
                                },
                                [[7], [9]],
                            ],
                            label='Asia',
                        ),
                    ],
                ),
            ),
            dict(
                type='dropdown',
                direction='down',
                x=0.25,
                y=button_layer_1_height,
                showactive=True,
                pad={"r": 10, "t": 10},
                font={'size': 10},
                xanchor='left',
                yanchor='top',
                buttons=list(
                    [
                        dict(
                            method='update',
                            args=[
                                {
                                    'y': [freq_covid_france['deaths']],
                                    'x': [freq_covid_france['dateRep']],
                                    'type': 'bar',
                                },
                                [[4], [5], [10], [13], [14]],
                            ],
                            label='March',
                        ),
                        dict(
                            method='update',
                            args=[
                                {
                                    'y': [freq_covid_france['deaths']],
                                    'x': [freq_covid_france['dateRep']],
                                    'type': 'bar',
                                },
                                [[0], [1], [2], [3], [6], [7], [8], [11], [12]],
                            ],
                            label='April',
                        ),
                        dict(
                            method='update',
                            args=[
                                {
                                    'y': [freq_covid_france['deaths']],
                                    'x': [freq_covid_france['dateRep']],
                                    'type': 'bar',
                                },
                                [9],
                            ],
                            label='May',
                        ),
                    ],
                ),
            ),
            dict(
                type='dropdown',
                direction='down',
                x=0.45,
                y=button_layer_1_height,
                showactive=True,
                pad={"r": 10, "t": 10},
                font={'size': 10},
                xanchor='left',
                yanchor='top',
                active=-1,
                buttons=list(
                    [
                        dict(
                            method='update',
                            args=['x', list_of_dep],
                            label='List of French Departments',
                        )
                    ],
                ),
            ),
        ],
    ),
)

fig.update_layout(
    annotations=[
        dict(
            text="List of<br>Countries",
            x=0,
            y=1.27,
            align="left",
            showarrow=False,
            font={'size': 10},
            xref='paper',
            yref='paper',
        ),
        dict(
            text="List of<br>Countries",
            x=0.2,
            y=1.27,
            align="left",
            showarrow=False,
            font={'size': 10},
            xref='paper',
            yref='paper',
        ),
        dict(
            text="List of<br>Departements",
            x=0.4,
            y=1.27,
            align='left',
            showarrow=False,
            font={'size': 10},
            xref='paper',
            yref='paper',
        ),
    ]
)


# img_width = 2100
# img_height = 1100
# scale_factor = 0.003
# fig.add_layout_image(
#     dict(
#         source='https://4.bp.blogspot.com/_tCcjI6S-GTw/TIvnlg3wNrI/AAAAAAAACLA/FK3tliXjovE/s1600/Crying+bum.jpg',
#         x=0,
#         sizex=img_width * scale_factor,
#         y=img_height * scale_factor,
#         sizey=img_height * scale_factor,
#         xref="x",
#         yref="y",
#         opacity=1.0,
#         layer="below",
#         sizing="stretch",
#     ),
#     row=2,
#     col=1,
# )

fig.show()
plot(fig)
