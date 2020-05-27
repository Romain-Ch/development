#!/usr/bin/env python3
# -*- coding: utf-8 -*-

### import packages
import pandas as pd
import numpy as np

from datetime import date, timedelta
from time import strftime, gmtime

import plotly.graph_objects as go

from plotly.subplots import make_subplots
from plotly.offline import plot



### import files


# test = pd.read_csv('https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv', sep=',')

# COVID-19 world data
df_covid_monde = pd.read_csv(
    'https://opendata.ecdc.europa.eu/covid19/casedistribution/csv', sep=','
)

df_covid_monde['dateRep'] = pd.to_datetime(df_covid_monde[['year', 'month', 'day']])
df_covid_monde['week'] = (
    pd.to_datetime(df_covid_monde[['year', 'month', 'day']])
    .dt.strftime('%V')
    .astype('int')
)

df_covid_monde = df_covid_monde.sort_values(
    by=['countriesAndTerritories', 'dateRep'], ascending=True
)


today = date.today() - timedelta(6)
date_of_today = (
    today.strftime('%Y-%m-%d') + '-' + strftime('%Hh%M', gmtime(60 * 60 * 19))
)

uri = (
    f'https://static.data.gouv.fr/resources/'
    f'donnees-hospitalieres-relatives-a-lepidemie-de-covid-19/'
    f'20200519-190024/donnees-hospitalieres-etablissements-covid19-'
    f'{date_of_today}'
    f'.csv'
)

# import COVID-19 french data
df_covid_det_france = pd.read_csv(uri, sep=';', parse_dates=True)


### merging

### dataframe infos
df_covid_monde.info()
df_covid_monde.isnull().sum()

df_covid_det_france.info()
df_covid_det_france.isnull().sum()


### filter, aggregating / grouping columns
freq_covid_monde = (
    df_covid_monde.groupby(['countriesAndTerritories', 'continentExp'])[
        ['cases', 'deaths']
    ]
    .sum()
    .sort_values(by='cases', ascending=False)[0:10]
    .reset_index()
    .rename(columns={"index": "x"})
)

df_covid_monde2 = pd.merge(
    df_covid_monde[(df_covid_monde['month'] >= 3) & (df_covid_monde['year'] > 2019)],
    freq_covid_monde['countriesAndTerritories'],
    on='countriesAndTerritories',
    how='inner',
).sort_values(by=['year', 'month', 'day'], ascending=True)

freq_month_covid_monde = (
    df_covid_monde2['month']
    .value_counts()
    .reset_index()
    .rename(columns={'index': 'month'})
)

df_covid_france = df_covid_monde[
    (df_covid_monde['countriesAndTerritories'] == 'France')
    & (df_covid_monde['month'] >= 3)
    & (df_covid_monde['year'] > 2019)
].sort_values(by=['year', 'month', 'day'], ascending=True)

freq_covid_france = (
    df_covid_france.groupby(['dateRep', 'month'])[['cases', 'deaths']]
    .sum()
    .sort_values(by='cases', ascending=False)[0:15]
    .reset_index()
    .rename(columns={'index': 'x'})
)

freq_covid_france_dep = (
    df_covid_det_france.groupby('dep')['nb']
    .sum()
    .sort_values(ascending=False)[0:10]
    .reset_index()
    .rename(columns={'index': 'x'})
)







fig = go.figure()
fig.add_trace(
    go.Scatter(
        x=freq_covid_monde['countriesAndTerritories'],
        y=freq_covid_monde['cases'],
        mode='markers+lines',
        name='World cases',
        marker_color='black',
    ),
)
fig.show()
plot(fig)

# df_covid_monde2.groupby(['countriesAndTerritories', 'month'])['dateRep'].count()

### cumulative percent
df_covid_monde2['death_pct'] = (
    df_covid_monde2['deaths'] / df_covid_monde2['popData2018']
)
df_covid_monde2['cases_pct'] = df_covid_monde2['cases'] / df_covid_monde2['popData2018']

df_covid_monde2['cum_death'] = df_covid_monde2['deaths'].cumsum()
df_covid_monde2['cum_cases'] = df_covid_monde2['cases'].cumsum()

df_covid_monde2['cum_death_pct'] = df_covid_monde2['death_pct'].cumsum()
df_covid_monde2['cum_cases_pct'] = df_covid_monde2['cases_pct'].cumsum()

df_covid_france['death_pct'] = (
    df_covid_france['deaths'] / df_covid_france['popData2018']
)
df_covid_france['cases_pct'] = df_covid_france['cases'] / df_covid_france['popData2018']


df_covid_france['cum_death_pct'] = df_covid_france['death_pct'].cumsum()
df_covid_france['cum_cases_pct'] = df_covid_france['cases_pct'].cumsum()

df_covid_france['cum_death'] = df_covid_france['deaths'].cumsum()
df_covid_france['cum_cases'] = df_covid_france['cases'].cumsum()


pie_values = freq_covid_france_dep['nb'].tolist()
pie_labels = freq_covid_france_dep['dep'].tolist()

list_of_countries = freq_covid_monde['countriesAndTerritories'].values.tolist()

list_of_dep = freq_covid_france_dep.index.tolist()


for val in freq_covid_monde['countriesAndTerritories']:
    print(
        df_covid_monde2[df_covid_monde2['countriesAndTerritories'] == val][
            'cum_death_pct'
        ].head()
    )

for val_month in df_covid_monde2.month.unique():
    print(df_covid_monde2[df_covid_monde2['month'] == val_month].head())

df_covid_monde2.groupby('dateRep')['cum_cases'].sum()
df_covid_monde2.dateRep.values.tolist()

# make a subplot
fig = make_subplots(
    rows=2,
    cols=2,
    specs=[
        [{'secondary_y': True, 'type': 'xy'}, {'type': 'xy'}],
        [{'type': 'xy'}, {'type': 'domain'}],
    ],
    subplot_titles=[
        'Top 10 of coutries the most infected',
        'Top 10 of french deaths/cases',
        '% of cumulative cases / deaths',
        'Top 10 of deaths per department',
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
for val in freq_covid_monde['countriesAndTerritories']:
    fig.add_trace(
        go.Scatter(
            x=df_covid_monde2[df_covid_monde2['countriesAndTerritories'] == val][
                'dateRep'
            ],
            y=df_covid_monde2[df_covid_monde2['countriesAndTerritories'] == val][
                'cum_death'
            ],
            mode='lines',
            name=val + ' deaths',
        ),
        row=1,
        col=2,
    )
    fig.add_trace(
        go.Scatter(
            x=df_covid_monde2[df_covid_monde2['countriesAndTerritories'] == val][
                'dateRep'
            ],
            y=df_covid_monde2[df_covid_monde2['countriesAndTerritories'] == val][
                'cum_cases'
            ],
            mode='lines',
            name=val + ' cases',
        ),
        row=1,
        col=2,
    ),

    fig.add_trace(
        go.Scatter(
            x=df_covid_monde2[df_covid_monde2['countriesAndTerritories'] == val][
                'dateRep'
            ],
            y=df_covid_monde2[df_covid_monde2['countriesAndTerritories'] == val][
                'cum_death_pct'
            ],
            name=val + ' death percent',
            mode='markers+lines',
        ),
        row=2,
        col=1,
    ),

    fig.add_trace(
        go.Scatter(
            x=df_covid_monde2[df_covid_monde2['countriesAndTerritories'] == val][
                'dateRep'
            ],
            y=df_covid_monde2[df_covid_monde2['countriesAndTerritories'] == val][
                'cum_cases_pct'
            ],
            name=val + ' cases percent',
            mode='markers+lines',
        ),
        row=2,
        col=1,
    ),


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
),


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
    showlegend=False,
    barmode='stack',
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
                            args=[
                                {
                                    'y': [
                                        freq_covid_monde['cases'],
                                        [freq_covid_monde['deaths'],],
                                    ],
                                },
                                [0],
                            ],
                            label='USA',
                        ),
                        dict(
                            method='update',
                            args=[
                                {
                                    'y': [
                                        freq_covid_monde['cases'],
                                        [freq_covid_monde['deaths'],],
                                    ],
                                },
                                [1],
                            ],
                            label='Brazil',
                        ),
                        dict(
                            method='update',
                            args=[
                                {
                                    'y': [
                                        freq_covid_monde['cases'],
                                        [freq_covid_monde['deaths'],],
                                    ],
                                },
                                [2],
                            ],
                            label='Russia',
                        ),
                        dict(
                            method='update',
                            args=[
                                {
                                    'y': [
                                        freq_covid_monde['cases'],
                                        [freq_covid_monde['deaths'],],
                                    ],
                                },
                                [3],
                            ],
                            label='UK',
                        ),
                        dict(
                            method='update',
                            args=[
                                {
                                    'y': [
                                        freq_covid_monde['cases'],
                                        [freq_covid_monde['deaths'],],
                                    ],
                                },
                                [4],
                            ],
                            label='Spain',
                        ),
                        dict(
                            method='update',
                            args=[
                                {
                                    'y': [
                                        freq_covid_monde['cases'],
                                        [freq_covid_monde['deaths'],],
                                    ],
                                },
                                [5],
                            ],
                            label='Italy',
                        ),
                        dict(
                            method='update',
                            args=[
                                {
                                    'y': [
                                        freq_covid_monde['cases'],
                                        [freq_covid_monde['deaths'],],
                                    ],
                                },
                                [6],
                            ],
                            label='Germany',
                        ),
                        dict(
                            method='update',
                            args=[
                                {
                                    'y': [
                                        freq_covid_monde['cases'],
                                        [freq_covid_monde['deaths'],],
                                    ],
                                },
                                [7],
                            ],
                            label='Turkey',
                        ),
                        dict(
                            method='update',
                            args=[
                                {
                                    'y': [
                                        freq_covid_monde['cases'],
                                        [freq_covid_monde['deaths'],],
                                    ],
                                },
                                [8],
                            ],
                            label='France',
                        ),
                        dict(
                            method='update',
                            args=[
                                {
                                    'y': [
                                        freq_covid_monde['cases'],
                                        [freq_covid_monde['deaths'],],
                                    ],
                                },
                                [9],
                            ],
                            label='Iran',
                        ),
                    ],
                ),
            ),
        ],
    ),
),


# {
#     'y': [
#         df_covid_monde2[
#             df_covid_monde2[
#                 'countriesAndTerritories'
#             ]
#             == val_countries
#         ]['cum_death'],
#         df_covid_monde2[
#             df_covid_monde2[
#                 'countriesAndTerritories'
#             ]
#             == val_countries
#         ]['cum_cases'],
#     ],
# },

# dict(
#     type='dropdown',
#     direction='down',
#     x=0.25,
#     y=button_layer_1_height,
#     showactive=True,
#     pad={"r": 10, "t": 10},
#     font={'size': 10},
#     xanchor='left',
#     yanchor='top',
#     buttons=list(
#         [
#             dict(
#                 method='update',
#                 args=[
#                     {
#                         'y': [
#                             df_covid_monde2[
#                                 df_covid_monde2['month'] == val_month
#                             ]['cum_death']
#                             for val_month in df_covid_monde2.month.unique()
#                         ],
#                     },
#                 ],
#                 label='deaths',
#             ),
#             dict(
#                 method='update',
#                 args=[
#                     {
#                         'y': [
#                             df_covid_monde2[
#                                 df_covid_monde2['month'] == val_month
#                             ]['cum_cases']
#                             for val_month in df_covid_monde2.month.unique()
#                         ],
#                     },
#                 ],
#                 label='cases',
#             ),
#         ],
#     ),
# ),
# dict(
#     type='dropdown',
#     direction='down',
#     x=0.45,
#     y=button_layer_1_height,
#     showactive=True,
#     pad={"r": 10, "t": 10},
#     font={'size': 10},
#     xanchor='left',
#     yanchor='top',
#     active=-1,
#     buttons=list(
#         [
#             dict(
#                 method='update',
#                 args=['x', list_of_dep],
#                 label='List of French Departments',
#             )
#         ],
#     ),
# ),


# fig.update_layout(
#     annotations=[
#         dict(
#             text="Continents",
#             x=0,
#             y=1.29,
#             align="left",
#             showarrow=False,
#             font={'size': 10},
#             xref='paper',
#             yref='paper',
#         ),
#         dict(
#             text="Type of data",
#             x=0.2,
#             y=1.29,
#             align="left",
#             showarrow=False,
#             font={'size': 10},
#             xref='paper',
#             yref='paper',
#         ),
#         dict(
#             text="List of<br>Departements",
#             x=0.4,
#             y=1.29,
#             align='left',
#             showarrow=False,
#             font={'size': 10},
#             xref='paper',
#             yref='paper',
#         ),
#     ],
# )
#
#
# # img_width = 2100
# # img_height = 1100
# # scale_factor = 0.003
# # fig.add_layout_image(
# #     dict(
# #         source='https://4.bp.blogspot.com/_tCcjI6S-GTw/TIvnlg3wNrI/AAAAAAAACLA/FK3tliXjovE/s1600/Crying+bum.jpg',
# #         x=0,
# #         sizex=img_width * scale_factor,
# #         y=img_height * scale_factor,
# #         sizey=img_height * scale_factor,
# #         xref="x",
# #         yref="y",
# #         opacity=1.0,
# #         layer="below",
# #         sizing="stretch",
# #     ),
# #     row=2,
# #     col=1,
# # )
#
fig.show()
plot(fig)
