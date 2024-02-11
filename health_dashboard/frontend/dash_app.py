from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd

df = pd.read_csv('data/health_data.csv')
metric_names = df.columns[1:]


app = Dash(__name__)

app.layout = html.Div([
    html.H1(children='Health Metrics', style={'textAlign':'center'}),
    dcc.Dropdown(metric_names, 'sleep_score', id='dropdown-selection'),
    dcc.Graph(id='graph-content')
])

@callback(
    Output('graph-content', 'figure'),
    Input('dropdown-selection', 'value')
)
def update_graph(value):
    x = df['day']
    y = df[value]
    fig = px.line(x=x, y=y, title=f'{value} over time')
    return fig

if __name__ == '__main__':
    app.run(debug=True)
