### import packages

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

import dash
import dash_core_components as dcc
import dash_html_components as html

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


def top(ligne):
    val = ''
    if ligne['cases'] < 0:
        val = 'lt 0'
    elif ligne['cases'] == 0:
        val = '0'
    elif (ligne['cases'] > 0) and (ligne['cases'] < 50):
        val = 'lt 50'
    elif (ligne['cases'] >= 50) and (ligne['cases'] < 100):
        val = '50-100'
    elif (ligne['cases'] >= 100) and (ligne['cases'] <= 300):
        val = '100-300'
    elif ligne['cases'] > 300:
        val = 'gt 300'
    return val


df_covid_monde['cum_days'] = df_covid_monde.apply(top, axis=1)

df_covid_monde.cum_days.value_counts()


freq_covid_cases = (
    df_covid_monde[
        (df_covid_monde['cum_days'] != 'lt 0') & (df_covid_monde['cum_days'] != '0')
    ]
    .groupby(['countriesAndTerritories', 'dateRep', 'cum_days'])['cases']
    .sum()
    .groupby(level=[0])
    .cumsum()
    .reset_index()
)

freq_covid_cum_days = (
    df_covid_monde[
        (df_covid_monde['cum_days'] != 'lt 0') & (df_covid_monde['cum_days'] != '0')
    ]
    .groupby(['countriesAndTerritories', 'dateRep'])['cum_days']
    .count()
    .groupby(level=[0])
    .cumsum()
    .reset_index()
    .rename(columns={'cum_days': 'freq_days'})
)

df_world_cum_cases = pd.merge(
    freq_covid_cases,
    freq_covid_cum_days[['countriesAndTerritories', 'dateRep', 'freq_days']],
    on=['countriesAndTerritories', 'dateRep'],
    how='left',
)


fig = px.line(
    df_world_cum_cases,
    x='freq_days',
    y='cases',
    log_y=True,
    line_group='countriesAndTerritories',
    color='countriesAndTerritories',
    hover_name='countriesAndTerritories',
)

app = dash.Dash()

app.layout = html.Div(children=[
    html.H1(children ='Covid-19 cases since 100 cases reached'),
    dcc.Graph(
        id='Pandemic-situation',
        figure={

        }
    )
])

fig.update_layout(
    title={
        'text': 'Covid-19 cases since 100 cases reached',
        'y': 0.95,
        'x': 0.4,
        'xanchor': 'center',
        'yanchor': 'top',
    },
    yaxis_title='total cases (log scale)',
    xaxis_title='days since 100 cases in a week reached',
    legend_title_text='Countries',
    annotations=[
        dict(
            text="cases buckets",
            x=0,
            y=1.29,
            align="left",
            showarrow=False,
            font={'size': 10},
            xref='paper',
            yref='paper',
        ),
    ],
)
fig.show()
