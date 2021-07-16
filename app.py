#!/usr/bin/env python

### import packages
import io

import dash
import dash_core_components as dcc
import dash_html_components as html
import flask
import pandas as pd
import plotly.graph_objects as go
import requests

# ignore certificate verification failure
r = requests.get(
    "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv",
    verify=False,
)

# COVID-19 world data
covid_monde = pd.read_csv(
    io.StringIO(r.content.decode("utf-8")), parse_dates=True, low_memory=False
)


covid_monde.continent.value_counts()

covid_monde["time"] = pd.to_datetime(covid_monde["date"])
covid_monde["week"] = (
    pd.to_datetime(covid_monde["time"]).dt.strftime("%V").astype("int")
)
covid_monde["month"] = covid_monde["time"].dt.month
covid_monde["abb_month"] = covid_monde["time"].dt.strftime("%b")

covid_location = covid_monde[covid_monde["location"] != "World"].sort_values(
    by=["location", "time"], ascending=True
)

covid_location["continent"] = covid_location["continent"].str.lower()


def top(ligne) -> str:
    val = ""
    if ligne["new_cases"] < 0:
        val = "lt 0"
    elif ligne["new_cases"] == 0:
        val = "0"
    elif (ligne["new_cases"] > 0) and (ligne["new_cases"] < 50):
        val = "lt 50"
    elif (ligne["new_cases"] >= 50) and (ligne["new_cases"] < 100):
        val = "50-100"
    elif (ligne["new_cases"] >= 100) and (ligne["new_cases"] <= 300):
        val = "100-300"
    elif ligne["new_cases"] > 300:
        val = "gt 300"
    return val


covid_location["bracket"] = covid_location.apply(top, axis=1)

covid_location.bracket.value_counts()


agg_covid_cases = (
    covid_location[
        (covid_location["bracket"] != "lt 0") & (covid_location["bracket"] != "0")
    ]
    .groupby(["location", "time", "bracket"])["new_cases"]
    .sum()
    .groupby(level=[0])
    .cumsum()
    .reset_index()
)

agg_covid_cum_days = (
    covid_location[
        (covid_location["bracket"] != "lt 0") & (covid_location["bracket"] != "0")
    ]
    .groupby(["location", "time"])["bracket"]
    .count()
    .groupby(level=[0])
    .cumsum()
    .reset_index()
    .rename(columns={"bracket": "cum_days"})
)

world_cum_cases = pd.merge(
    agg_covid_cases,
    agg_covid_cum_days[["location", "time", "cum_days"]],
    on=["location", "time"],
    how="left",
)

agg_top_30 = pd.merge(
    covid_location[["location", "time", "date", "new_cases", "new_deaths"]],
    (
        covid_location.groupby("location")[["new_cases", "new_deaths"]]
        .sum()
        .sort_values(by=["new_cases", "new_deaths"], ascending=False)[0:30]
        .reset_index()
    )["location"],
    on=["location"],
    how="inner",
)

agg_top_30_cases = (
    covid_location[
        (covid_location["bracket"] != "lt 0") & (covid_location["bracket"] != "0")
    ]
    .groupby("location")["new_cases"]
    .sum()
    .sort_values(ascending=False)[0:30]
    .reset_index()
    .rename(columns={"index": "x"})
)

top_30_cases = pd.merge(
    world_cum_cases,
    agg_top_30_cases["location"],
    on=["location"],
    how="inner",
)

covid_countries = (
    covid_location[covid_location["time"] > "2020-01-01"]
    .groupby(["location", "iso_code", "continent", "month", "abb_month"])[
        ["new_cases", "new_deaths"]
    ]
    .sum()
    .reset_index()
)


case_death_pop = pd.merge(
    (
        covid_location[covid_location["time"] > "2020-01-01"]
        .groupby(["location", "month", "abb_month", "population", "life_expectancy"])[
            ["new_cases", "new_deaths"]
        ]
        .sum()
        .groupby(level=[0])
        .cumsum()
        .reset_index()
    ),
    (
        covid_location.groupby("location")[["new_cases", "new_deaths"]]
        .sum()
        .sort_values(by="new_cases", ascending=False)[0:30]
        .reset_index()
    )["location"],
    on=["location"],
    how="inner",
)

case_death_pop["deaths_per_pop"] = (
    case_death_pop["new_deaths"] / case_death_pop["population"]
)
case_death_pop["cases_per_pop"] = (
    case_death_pop["new_cases"] / case_death_pop["population"]
)

# Initialize the App
external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]
server = flask.Flask(__name__)  # define flask app.server
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, server=server)

countries = top_30_cases["location"].unique()
countries2 = agg_top_30["location"].unique()
months = covid_countries["month"].unique()
continent = covid_countries["continent"].unique()

trace_1 = go.Scatter(
    x=top_30_cases[top_30_cases["location"] == "United States"]["cum_days"],
    y=top_30_cases[top_30_cases["location"] == "United States"]["new_cases"],
    mode="lines",
    name="United States",
    line=dict(width=1, color="rgba(22, 128, 203, 1)"),
)

line_layout = go.Layout(
    title="Covid-19 cases since 100 cases reached",
    yaxis={"title": "total cases (log scale)", "type": "log"},
    xaxis={"title": "days since 100 cases in a week reached"},
    autosize=True,
    showlegend=True,
    margin=dict(l=20, r=0, b=20, t=40),
    hovermode="closest",
    plot_bgcolor="#F9F9F9",
    paper_bgcolor="#F9F9F9",
    legend=dict(font=dict(size=10), orientation="h"),
)

line_fig = go.Figure(data=[trace_1], layout=line_layout)


# Create App Layout
app.layout = html.Div(
    [
        html.Div(
            [html.H1("Dash pandemic situation")],
            style={"margin-bottom": "50px", "backgroundColor": "#F9F9F9"},
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.P("Select the country", className="control_label"),
                        dcc.Dropdown(
                            id="countries-filter1",
                            options=[{"label": i, "value": i} for i in countries],
                            value="United States",
                            className="dcc_control",
                        ),
                        html.P("Select an indicator", className="control_label"),
                        dcc.Dropdown(
                            id="selected-indicator",
                            options=[
                                {"label": "cases", "value": "new_cases"},
                                {"label": "deaths", "value": "new_deaths"},
                            ],
                            value="new_deaths",
                            className="dcc_control",
                        ),
                        html.P("Month of the year", className="control_label"),
                        dcc.Slider(
                            id="months-filter",
                            value=covid_countries["month"].max(),
                            min=covid_countries["month"].min(),
                            max=covid_countries["month"].max(),
                            marks={str(month): str(month) for month in months},
                            className="dcc_control",
                        ),
                        html.P("Select the continent", className="control_label"),
                        dcc.Dropdown(
                            id="continent-filter",
                            options=[
                                {"label": "World", "value": "world"},
                                {"label": "Africa", "value": "africa"},
                                {"label": "Asia", "value": "asia"},
                                {"label": "Europe", "value": "europe"},
                                {"label": "North America", "value": "north america"},
                                {"label": "South America", "value": "south america"},
                            ],
                            value="world",
                            className="dcc_control",
                        ),
                    ],
                    style={"display": "inline-block", "width": "15%"},
                    className="four columns",
                    id="filter-options1",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                dcc.Graph(id="line-filter-indicator", figure=line_fig),
                            ],
                            className="five columns",
                        ),
                        html.Div(
                            [dcc.Graph(id="choropleth-map")],
                            className="five columns",
                        ),
                    ],
                ),
            ],
            className="rows",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.P("", className="control_label"),
                        dcc.Dropdown(
                            id="countries-filter2",
                            options=[{"label": i, "value": i} for i in countries2],
                            value="United States",
                            className="dcc_control",
                        ),
                        html.P("Select an indicator", className="control_label"),
                        dcc.Dropdown(
                            id="selected-indicator2",
                            options=[
                                {"label": "% cases", "value": "cases_per_pop"},
                                {"label": "% deaths", "value": "deaths_per_pop"},
                            ],
                            value="cases_per_pop",
                            className="dcc_control",
                        ),
                    ],
                    style={"display": "inline-block", "width": "15%"},
                    className="four columns",
                    id="filter-options2",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                dcc.Graph(id="bar-filter-indicator"),
                            ],
                            className="five columns",
                        ),
                        html.Div(
                            [
                                dcc.Graph(id="bubble-chart"),
                            ],
                            className="five columns",
                        ),
                    ],
                ),
            ],
            className="rows",
        ),
    ],
    style={"display": "flex", "flex-direction": "column"},
)


@app.callback(
    dash.dependencies.Output("line-filter-indicator", "figure"),
    [dash.dependencies.Input("countries-filter1", "value")],
)
def upd_line_plots(country_value):

    out_of_US = top_30_cases[top_30_cases["location"] != "United States"]

    trace_1 = go.Scatter(
        x=top_30_cases[top_30_cases["location"] == "United States"]["cum_days"],
        y=top_30_cases[top_30_cases["location"] == "United States"]["new_cases"],
        mode="lines",
        line=dict(width=1, color="rgba(22, 128, 203, 1)"),
        name="United States",
    )
    trace_2 = go.Scatter(
        x=out_of_US[out_of_US["location"] == country_value]["cum_days"],
        y=out_of_US[out_of_US["location"] == country_value]["new_cases"],
        mode="lines",
        line=dict(width=1, color="rgba(193, 67, 22, 1)"),
        name=country_value,
    )

    fig = go.Figure(data=[trace_1, trace_2], layout=line_layout)
    return fig


@app.callback(
    dash.dependencies.Output("bar-filter-indicator", "figure"),
    [dash.dependencies.Input("countries-filter2", "value")],
)
def upd_charts_plots(country_val):

    dff = agg_top_30[
        (agg_top_30["date"] >= "2020-03-01")
        & (agg_top_30["new_cases"] >= 0)
        & (agg_top_30["new_deaths"] >= 0)
    ]

    data = [
        dict(
            type="bar",
            x=dff[dff["location"] == country_val]["date"],
            y=dff[dff["location"] == country_val]["new_cases"],
            name="Cases",
            marker_color="rgba(22, 128, 203, 1)",
            yaxis="y",
            offsetgroup=1,
        ),
        dict(
            type="bar",
            x=dff[dff["location"] == country_val]["date"],
            y=dff[dff["location"] == country_val]["new_deaths"],
            name="Deaths",
            marker_color="rgba(193, 67, 22, 0.5)",
            yaxis="y2",
            offsetgroup=2,
        ),
    ]

    bar_layout = go.Layout(
        title="Cases & Deaths",
        autosize=True,
        showlegend=True,
        yaxis2=dict(overlaying="y", side="right"),
        margin=dict(t=30, b=0, l=5, r=5),
        hovermode="closest",
        plot_bgcolor="#F9F9F9",
        paper_bgcolor="#F9F9F9",
        legend=dict(font=dict(size=10), orientation="h"),
    )

    bar_fig = go.Figure(data=data, layout=bar_layout)
    return bar_fig


@app.callback(
    dash.dependencies.Output("choropleth-map", "figure"),
    [
        dash.dependencies.Input("selected-indicator", "value"),
        dash.dependencies.Input("months-filter", "value"),
        dash.dependencies.Input("continent-filter", "value"),
    ],
)
def choropleth(selected_indic, month_val, continent_val):

    covid_countries["str_val_country"] = (
        covid_countries["location"] + ": " + covid_countries[selected_indic].apply(str)
    )

    dff = covid_countries[
        (covid_countries["month"] >= month_val)
        & (covid_countries["month"] <= month_val)
    ]

    trace = go.Choropleth(
        locations=dff["iso_code"],
        z=dff[selected_indic],
        text=dff["str_val_country"],
        hoverinfo="text",
        autocolorscale=False,
        reversescale=True,
        colorscale="RdBu",
        marker={"line": {"color": "rgb(180,180,180)", "width": 0.1}},
        colorbar={
            "thickness": 10,
            "len": 0.3,
            "x": 1,
            "y": 0.5,
            "title": {"text": "persons", "side": "bottom"},
        },
    )

    map_layout = go.Layout(
        title="Evolution of the pandemic situation in the world",
        autosize=True,
        hovermode="closest",
        geo_scope=continent_val,
        plot_bgcolor="#F9F9F9",
        paper_bgcolor="#F9F9F9",
        margin=dict(l=20, r=0, b=20, t=40),
        legend=dict(font=dict(size=10), orientation="h"),
        geo={
            "showframe": False,
            "showcoastlines": False,
            "projection": {"type": "miller"},
        },
    )

    map_fig = go.Figure(data=trace, layout=map_layout)

    return map_fig


@app.callback(
    dash.dependencies.Output("bubble-chart", "figure"),
    [
        dash.dependencies.Input("selected-indicator2", "value"),
        dash.dependencies.Input("countries-filter2", "value"),
    ],
)
def upd_bubble_chart(selected_indic, country_val):

    color = [float(val) for val in case_death_pop.life_expectancy]
    size = [val + val ** 4 for val in range(len(case_death_pop))]

    data = go.Scatter(
        x=case_death_pop[case_death_pop["location"] == country_val]["abb_month"],
        y=case_death_pop[case_death_pop["location"] == country_val][selected_indic],
        mode="markers",
        marker=dict(sizemode="area", color=color, size=size),
    )

    bubble_layout = go.Layout(
        title="% of cumulative cases and deaths per pop",
        autosize=True,
        hovermode="closest",
        yaxis={"type": "log", "tickformat": ".1%"},
        plot_bgcolor="#F9F9F9",
        paper_bgcolor="#F9F9F9",
        margin=dict(t=30, b=0, l=5, r=5),
        legend=dict(font=dict(size=10), orientation="h"),
    )

    bubble_fig = go.Figure(data=data, layout=bubble_layout)

    return bubble_fig


# Run the App
if __name__ == "__main__":
    app.run_server(debug=True)
