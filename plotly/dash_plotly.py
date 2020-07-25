### import packages

import pandas as pd
import plotly.graph_objects as go
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html


# COVID-19 world data
covid_monde = pd.read_csv(
    'https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv',
    parse_dates=True,
)

covid_monde['time'] = pd.to_datetime(covid_monde['date'])
covid_monde['week'] = (
    pd.to_datetime(covid_monde['time']).dt.strftime('%V').astype('int')
)
covid_monde['month'] = covid_monde['time'].dt.month

covid_location = covid_monde[covid_monde['location'] != 'World'].sort_values(
    by=['location', 'time'], ascending=True
)

def top(ligne):
    val = ''
    if ligne['new_cases'] < 0:
        val = 'lt 0'
    elif ligne['new_cases'] == 0:
        val = '0'
    elif (ligne['new_cases'] > 0) and (ligne['new_cases'] < 50):
        val = 'lt 50'
    elif (ligne['new_cases'] >= 50) and (ligne['new_cases'] < 100):
        val = '50-100'
    elif (ligne['new_cases'] >= 100) and (ligne['new_cases'] <= 300):
        val = '100-300'
    elif ligne['new_cases'] > 300:
        val = 'gt 300'
    return val


covid_location['bracket'] = covid_location.apply(top, axis=1)

covid_location.bracket.value_counts()


agg_covid_cases = (
    covid_location[
        (covid_location['bracket'] != 'lt 0') & (covid_location['bracket'] != '0')
    ]
    .groupby(['location', 'time', 'bracket'])['new_cases']
    .sum()
    .groupby(level=[0])
    .cumsum()
    .reset_index()
)

agg_covid_cum_days = (
    covid_location[
        (covid_location['bracket'] != 'lt 0') & (covid_location['bracket'] != '0')
    ]
    .groupby(['location', 'time'])['bracket']
    .count()
    .groupby(level=[0])
    .cumsum()
    .reset_index()
    .rename(columns={'bracket': 'cum_days'})
)

world_cum_cases = pd.merge(
    agg_covid_cases,
    agg_covid_cum_days[['location', 'time', 'cum_days']],
    on=['location', 'time'],
    how='left',
)

agg_top_30 = pd.merge(
    covid_location[['location', 'time', 'date', 'new_cases', 'new_deaths']],
    (
        covid_location.groupby('location')[['new_cases', 'new_deaths']]
        .sum()
        .sort_values(by=['new_cases', 'new_deaths'], ascending=False)[0:30]
        .reset_index()
    )['location'],
    on=['location'],
    how='inner',
)

agg_top_30_cases = (
    covid_location[
        (covid_location['bracket'] != 'lt 0') & (covid_location['bracket'] != '0')
    ]
    .groupby('location')['new_cases']
    .sum()
    .sort_values(ascending=False)[0:30]
    .reset_index()
    .rename(columns={'index': 'x'})
)

top_30_cases = pd.merge(
    world_cum_cases, agg_top_30_cases['location'], on=['location'], how='inner',
)

covid_countries = (
    covid_location[covid_location['time'] > '2020-01-01']
    .groupby(['location', 'iso_code', 'month'])[['new_cases', 'new_deaths']]
    .sum()
    .reset_index()
)

# covid_location[(covid_location['location'] == 'France') & (covid_location['time'] <= '2020-07-07')].groupby('location')['new_tests'].sum()

case_death_pop = pd.merge(
    (
        covid_location[covid_location['time'] > '2020-01-01']
        .groupby(['location', 'month', 'population', 'life_expectancy'])[
            ['new_cases', 'new_deaths']
        ]
        .sum()
        .groupby(level=[0])
        .cumsum()
        .reset_index()
    ),
    (
        covid_location.groupby('location')[['new_cases', 'new_deaths']]
        .sum()
        .sort_values(by='new_cases', ascending=False)[0:30]
        .reset_index()
    )['location'],
    on=['location'],
    how='inner',
)

case_death_pop['deaths_per_pop'] = (
    case_death_pop['new_deaths'] / case_death_pop['population']
)
case_death_pop['cases_per_pop'] = (
    case_death_pop['new_cases'] / case_death_pop['population']
)

# top_15_cases['month'] = top_15_cases['time'].dt.month

# Initialize the App
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

countries = top_30_cases['location'].unique()
countries2 = agg_top_30['location'].unique()
months = covid_countries['month'].unique()

trace_1 = go.Scatter(
    x=top_30_cases[top_30_cases['location'] == 'United States']['cum_days'],
    y=top_30_cases[top_30_cases['location'] == 'United States']['new_cases'],
    mode='lines',
    name='United States',
    line=dict(width=1, color='rgba(22, 128, 203, 1)'),
)

line_layout = go.Layout(
    title='Covid-19 cases since 100 cases reached',
    yaxis={'title': 'total cases (log scale)', 'type': 'log'},
    xaxis={'title': 'days since 100 cases in a week reached'},
    autosize=True,
    showlegend=True,
    margin=dict(l=20, r=0, b=20, t=40),
    hovermode="closest",
    plot_bgcolor='#F9F9F9',
    paper_bgcolor='#F9F9F9',
    legend=dict(font=dict(size=10), orientation='h'),
)

line_fig = go.Figure(data=[trace_1], layout=line_layout)


# Create App Layout
app.layout = html.Div(
    [
        html.Div(
            [html.H1('Dash pandemic situation')],
            style={'margin-bottom': '50px', 'backgroundColor': '#ffffff'},
        ),
        html.Div(
            [
                html.Div([
                    dcc.Graph(id='line-filter-indicator', figure=line_fig),
                    dcc.Graph(id='bar-filter-indicator')],
                    style={'display':'inline-block'},
                    className='six columns',
                ),
                html.Div([
                    dcc.Graph(id='choropleth-map'),
                    dcc.Graph(id='bubble-chart')],
                    style={'display': 'inline-block'},
                    className='six columns',
                ),
            ],
            style={'display': 'inline-block'},
        ),
        html.Div(
            [
                html.P('Filter by location', className='control_label'),
                dcc.Dropdown(
                    id='countries-filter1',
                    options=[{'label': i, 'value': i} for i in countries],
                    value='United States',
                    className='dcc_control',
                ),
                html.P('Select an indicator', className='control_label'),
                dcc.Dropdown(
                    id='selected-indicator',
                    options=[
                        {'label': 'cases', 'value': 'new_cases'},
                        {'label': 'deaths', 'value': 'new_deaths'},
                    ],
                    value='new_deaths',
                ),
                html.P('Select a period', className='control_label'),
                dcc.Slider(
                    id='months-filter',
                    value=covid_countries['month'].max(),
                    min=covid_countries['month'].min(),
                    max=covid_countries['month'].max(),
                    marks={str(month): str(month) for month in months},
                ),
            ],
            style={
                'display': 'inline-block',
                'width': '33%',
                'padding': '15px 10px 5px',
            },
            # className='two columns',
        ),
        html.Div(
            [
                html.P('', className='control_label'),
                dcc.Dropdown(
                    id='countries-filter2',
                    options=[{'label': i, 'value': i} for i in countries2],
                    value='United States',
                    className='dcc_control',
                ),
                html.P('Select an indicator', className='control_label'),
                dcc.Dropdown(
                    id='selected-indicator2',
                    options=[
                        {'label': '% cases', 'value': 'cases_per_pop'},
                        {'label': '% deaths', 'value': 'deaths_per_pop'},
                    ],
                    value='cases_per_pop',
                ),
            ],
            style={
                'display': 'inline-block',
                'width': '49%',
            },
            # className='two columns',
        ),
        # html.Div(
        #     [
        #         html.P('Select an indicator', className='control_label'),
        #         dcc.Dropdown(
        #             id='selected-indicator2',
        #             options=[
        #                 {'label': '% cases', 'value': 'cases_per_pop'},
        #                 {'label': '% deaths', 'value': 'deaths_per_pop'},
        #             ],
        #             value='cases_per_pop',
        #         ),
        #     ],
        #     style={
        #         'display': 'inline-block',
        #         'width': '25%',
        #         'margin-left': 'auto',
        #         'margin-top': 'auto',
        #     },
        #     className='eight columns',
        # ),
        # html.Div(
        #     [
        #         html.P('Select a period', className='control_label'),
        #         dcc.Slider(
        #             id='months-filter',
        #             value=covid_countries['month'].max(),
        #             min=covid_countries['month'].min(),
        #             max=covid_countries['month'].max(),
        #             marks={str(month): str(month) for month in months},
        #         ),
        #     ],
        #     style={
        #         'display': 'inline-block',
        #         'width': '25%',
        #         'margin-left': 'auto',
        #         'margin-bottom': 'auto',
        #     },
        #     className='ten columns',
        # ),
    ],
    style={'display': 'flex', 'flex-direction': 'column'},
    className='row',
)


@app.callback(
    dash.dependencies.Output('line-filter-indicator', 'figure'),
    [dash.dependencies.Input('countries-filter1', 'value')],
)
def upd_line_plots(country_value):

    out_of_US = top_30_cases[top_30_cases['location'] != 'United States']

    trace_1 = go.Scatter(
        x=top_30_cases[top_30_cases['location'] == 'United States']['cum_days'],
        y=top_30_cases[top_30_cases['location'] == 'United States']['new_cases'],
        mode='lines',
        line=dict(width=1, color='rgba(22, 128, 203, 1)'),
        name='United States',
    )
    trace_2 = go.Scatter(
        x=out_of_US[out_of_US['location'] == country_value]['cum_days'],
        y=out_of_US[out_of_US['location'] == country_value]['new_cases'],
        mode='lines',
        line=dict(width=1, color='rgba(193, 67, 22, 1)'),
        name=country_value,
    )

    fig = go.Figure(data=[trace_1, trace_2], layout=line_layout)
    return fig


@app.callback(
    dash.dependencies.Output('bar-filter-indicator', 'figure'),
    [dash.dependencies.Input('countries-filter2', 'value')],
)
def upd_charts_plots(country_val):

    dff = agg_top_30[
        (agg_top_30['date'] >= '2020-03-01')
        & (agg_top_30['new_cases'] >= 0)
        & (agg_top_30['new_deaths'] >= 0)
    ]

    data = [
        dict(
            type='bar',
            x=dff[dff['location'] == country_val]['date'],
            y=dff[dff['location'] == country_val]['new_cases'],
            name='Cases',
            marker_color='rgba(22, 128, 203, 1)',
            yaxis='y',
            offsetgroup=1,
        ),
        dict(
            type='bar',
            x=dff[dff['location'] == country_val]['date'],
            y=dff[dff['location'] == country_val]['new_deaths'],
            name='Deaths',
            marker_color='rgba(193, 67, 22, 0.5)',
            yaxis='y2',
            offsetgroup=2,
        ),
    ]

    bar_layout = go.Layout(
        title='Cases & Deaths',
        autosize=True,
        showlegend=True,
        yaxis2=dict(overlaying='y', side='right'),
        margin=dict(t=30, b=0, l=5, r=5),
        hovermode='closest',
        plot_bgcolor='#F9F9F9',
        paper_bgcolor='#F9F9F9',
        legend=dict(font=dict(size=10), orientation='h'),
    )

    bar_fig = go.Figure(data=data, layout=bar_layout)
    return bar_fig


@app.callback(
    dash.dependencies.Output('choropleth-map', 'figure'),
    [
        dash.dependencies.Input('selected-indicator', 'value'),
        dash.dependencies.Input('months-filter', 'value'),
    ],
)
def choropleth(selected_indic, month_val):

    covid_countries['str_val_country'] = (
        covid_countries['location'] + ": " + covid_countries[selected_indic].apply(str)
    )

    dff = covid_countries[
        (covid_countries['month'] >= month_val)
        & (covid_countries['month'] <= month_val)
    ]

    trace = go.Choropleth(
        locations=dff['iso_code'],
        z=dff[selected_indic],
        text=dff['str_val_country'],
        hoverinfo='text',
        autocolorscale=False,
        reversescale=True,
        colorscale='RdBu',
        marker={'line': {'color': 'rgb(180,180,180)', 'width': 0.1}},
        colorbar={
            'thickness': 10,
            'len': 0.3,
            'x': 1,
            'y': 0.5,
            'title': {'text': 'persons', 'side': 'bottom'},
        },
    )

    map_layout = go.Layout(
        title='Evolution of the pandemic situation in the world',
        autosize=True,
        hovermode='closest',
        plot_bgcolor='#F9F9F9',
        paper_bgcolor='#F9F9F9',
        margin=dict(l=20, r=0, b=20, t=40),
        legend=dict(font=dict(size=10), orientation='h'),
        geo={
            'showframe': False,
            'showcoastlines': False,
            'projection': {'type': 'miller'},
        },
    )

    map_fig = go.Figure(data=trace, layout=map_layout)

    return map_fig


@app.callback(
    dash.dependencies.Output('bubble-chart', 'figure'),
    [
        dash.dependencies.Input('selected-indicator2', 'value'),
        dash.dependencies.Input('countries-filter2', 'value'),
    ],
)
def upd_bubble_chart(selected_indic, country_val):

    color = [float(val) for val in case_death_pop.life_expectancy]
    size = [val+val**4 for val in range(len(case_death_pop))]

    data = go.Scatter(
        x=case_death_pop[case_death_pop['location'] == country_val]['month'],
        y=case_death_pop[case_death_pop['location'] == country_val][selected_indic],
        mode='markers',
        marker=dict(sizemode='area', color=color, size=size),
    )

    bubble_layout = go.Layout(
        title='% of cumulative cases and deaths per pop',
        autosize=True,
        hovermode='closest',
        yaxis={'type': 'log', 'tickformat': '.1%'},
        plot_bgcolor='#F9F9F9',
        paper_bgcolor='#F9F9F9',
        margin=dict(t=30, b=0, l=5, r=5),
        legend=dict(font=dict(size=10), orientation='h'),
    )

    bubble_fig = go.Figure(data=data, layout=bubble_layout)

    return bubble_fig


# Run the App
if __name__ == '__main__':
    app.run_server(debug=True, port=8000)
