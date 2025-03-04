from pydoc import classname
from dash import Dash, html, dcc, Input, Output, State
import plotly.express as px
import dash_bootstrap_components as dbc
import pandas as pd
from pandas_datareader import wb
import plotly.graph_objects as go

__author__ = 'Brevin Tating'
__credits__ = ['Brevin Tating']
__email__ = 'btating@westmont.edu'


app = Dash(__name__, external_stylesheets=[dbc.themes.LUMEN])

indicators = {
    "EG.ELC.ACCS.ZS": "Access to electricity (% of population)",
    "SP.DYN.IMRT.IN": "Mortality rate, infant (per 1,000 live births)"
}

countries = wb.get_countries()
print(countries)
countries["capitalCity"].replace({"": None}, inplace=True)
countries.dropna(subset=["capitalCity"], inplace=True)
countries = countries[countries["name"] != "Kosovo"]
countries = countries[countries["name"] != "Korea, Dem. People's Rep."]
countries = countries[["name", "iso3c"]]
countries = countries.rename(columns={"name": "country"})


# Fetch World Bank Data
def get_data():
    df = wb.download(indicator=list(indicators), country=countries["iso3c"], start=2004, end=2020)
    df = df.reset_index()

    df.year = df.year.astype(int)
    df = pd.merge(df, countries, on="country")
    df = df.rename(columns=indicators)
    #print(df.head().to_string())
    return df

df = get_data()

# Create Choropleth Map

# Dash Layout
app.layout = dbc.Container([
    dbc.Row(dbc.Col(html.H1("Electricity Access and its impact on Infant Mortality"), width=10)),
    dbc.Row([
        dbc.Col(dcc.Graph(id='choropleth-map', figure={}), width=5),
        dbc.Col(dcc.Graph(id='secondary-chart'), width=5)
    ]),
    dbc.Row([
        dbc.Col(dcc.RangeSlider(
            id='year-slider',
            min=2004, max=2020, step=1,
            value=[2004, 2020],
            marks={
                2004: "2004",
                2005: "'05",
                2006: "'06",
                2007: "'07",
                2008: "'08",
                2009: "'09",
                2010: "'10",
                2011: "'11",
                2012: "'12",
                2013: "'13",
                2014: "'14",
                2015: "'15",
                2016: "'16",
                2017: "'17",
                2018: "'18",
                2019: "'19",
                2020: "2020",
            }

        ), width=10)
    ]),

    dcc.Store(id="storage", storage_type="session", data={}),
    dcc.Interval(id="timer", interval=1000 * 60, n_intervals=0)
])

# Callbacks
@app.callback(Output("storage", "data"),
              Input("timer", "n_intervals"))

def store_data(n_time):
    dataframe = get_data()
    return dataframe.to_dict("records")

@app.callback(
    Output("choropleth-map", "figure"),
    Input("storage", "data")
)
def update_choropleth_map(stored_df):
    df = pd.DataFrame.from_records(stored_df)

    # Load GeoJSON for country shapes
    world_geojson = px.data.gapminder().query("year == 2007")  # Placeholder for GeoJSON data

    fig = px.choropleth(
        df,
        locations="iso3c",  # Country ISO code
        hover_data={"iso3c" : False, "country" : True},  # Show country names on hover
        scope="world",
    )

    # Remove color scale (no heatmap effect)
    fig.update_traces(marker=dict(line=dict(width=0.5, color='black')), showscale=False)

    # Fix projection and layout
    fig.update_layout(
        geo={"projection": {"type": "orthographic"}},
        margin=dict(l=0, r=0, t=0, b=0),
    )

    return fig


@app.callback(
    Output('secondary-chart', 'figure'),
    Input('choropleth-map', 'clickData'),  # Country selection
    Input('year-slider', 'value'),  # Year range selection
    Input('storage', 'data')  # Stored dataset
)
def update_chart(clickData, selected_years, stored_df):
    df = pd.DataFrame.from_records(stored_df)
    print(df.head())
    print(f"CLICK DATA: {clickData}")

    if clickData is None:
        return px.line(title="Select a country on the map")

    country = clickData['points'][0]['location']
    print(f"COUNTRY: {country}")
    df = df[df["iso3c"] == country]  # Filter by selected country
    print(df)

    # Apply year range filter
    df = df[df["year"].between(selected_years[0], selected_years[1])]

    print(f"DF: {df}" )
    if df.empty:
        return px.line(title=f"No data available for {country} in selected years")

    # Create dual-axis line graph
    fig = go.Figure()

    # Electricity Access Line (Y-Axis 1)
    fig.add_trace(go.Scatter(
        x=df["year"], y=df["Access to electricity (% of population)"],
        mode='lines+markers',
        name="Electricity Access (%)",
        yaxis="y1",
        line=dict(color="blue")
    ))

    # Infant Mortality Line (Y-Axis 2)
    fig.add_trace(go.Scatter(
        x=df["year"], y=df["Mortality rate, infant (per 1,000 live births)"],
        mode='lines+markers',
        name="Infant Mortality (per 1,000)",
        yaxis="y2",
        line=dict(color="red")
    ))

    # Set up the graph layout
    fig.update_layout(
        title=f"Electricity Access & Infant Mortality in {country}, {selected_years[0]}-{selected_years[1]}",
        xaxis=dict(title="Year", range=[selected_years[0], selected_years[1]]),  # Dynamic x-axis
        yaxis=dict(title="Electricity Access (%)", range=[0, 100], color="blue"),  # Fixed y1-axis
        yaxis2=dict(
            title="Infant Mortality (per 1,000)",
            range=[0, 100],  # Fixed y2-axis
            overlaying="y", side="right", color="red"
        )
    )

    return fig





if __name__ == '__main__':
    app.run_server(debug=True)
