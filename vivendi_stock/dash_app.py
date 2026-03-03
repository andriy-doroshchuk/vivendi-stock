from __future__ import annotations

import datetime
from dash import Dash, dcc, html, Input, Output, callback

from .core.vivendi_data import VivendiStock, STOCK
from .utils.config import config

# Module-level singleton — avoids reconstructing VivendiStock (disk read + potential
# API calls) on every Refresh button click.
_stock_data = VivendiStock()


def stock_graphs() -> html.Div:
    app_data = _stock_data
    app_data.update()

    def get_graph(key: str, name: str) -> html.Div:
        history, current_price, change_percent = app_data.get_data(key)

        if change_percent > 0:
            change_percent = f'+{change_percent}%'
            change_color = 'success'
        else:
            change_percent = f'{change_percent}%'
            change_color = 'danger'

        return html.Div(className='row', children=[
            html.Div(className='container', children=[
                html.Div(className='row', children=html.Hr()),
                html.Div(className='row', children=[
                    html.Div(className='col-sm-9', children=[
                        html.H4(className='text-left',
                                children=f'{name} ({key})')
                    ]),
                    html.Div(className='col-sm-2', children=[
                        html.H2(className='text-right', children=current_price)
                    ]),
                    html.Div(className='col-sm-1', children=[
                        html.H4(
                            className=f'text-left text-{change_color}', children=change_percent)
                    ])
                ]),
                html.Div(className='row', children=[
                    dcc.Graph(
                        id=f'stocks_graph_{key}',
                        figure={
                            'data': [{
                                'x': history.index,
                                'y': history,
                                'type': 'line',
                                'name': key
                            }],
                            'layout': {'height': 400}
                        },
                        config={
                            'displayModeBar': False,
                            'displaylogo': False,
                            'scrollZoom': False,
                            'staticPlot': True
                        }
                    )
                ])
            ])
        ])

    timestamp = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    graphs = [html.Div(className='center-align',
                       children=f'Generated {timestamp}')]
    graphs += [get_graph('STOCK.VALUE', 'Estimated stock value in AUD')]
    graphs += [get_graph(stock, STOCK[stock]['name']) for stock in STOCK]
    return html.Div(className='container', children=graphs)


app = Dash(
    'Stock tracker',
    assets_folder=f'{config.APP_ROOT}/static/stylesheets',
)

app.config['suppress_callback_exceptions'] = True
app.layout = html.Div(children=[
    html.H3(className='center-align big-Close',
            children='Vivendi Group Stock Value Tracker'),
    html.Div(className='container center-align', children=[
        html.Button(className='btn btn-primary',
                    id='refresh-button', n_clicks=0, children='Refresh')
    ]),
    html.Br(),
    html.Div(className='container', children=[
        html.Div(className='row', children=[
            html.Div(className='col-sm-9', children=[
                html.H4(className='text-left',
                        children='Estimated stock value in AUD at 01-03-2024')
            ]),
            html.Div(className='col-sm-2', children=[
                html.H2(className='text-right', children='17.403')
            ]),
            html.Div(className='col-sm-1', children=[])
        ])
    ]),
    html.Br(),
    html.Div(id='output-graphs')
])


@callback(Output('output-graphs', 'children'), Input('refresh-button', 'n_clicks'))
def update_graphs(_: int) -> html.Div:
    return stock_graphs()


if __name__ == '__main__':
    app.run(host=config.DASH_HOST, port=config.DASH_PORT,
            debug=config.DASH_DEBUG)
