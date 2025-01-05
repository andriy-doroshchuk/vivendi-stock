import time
from dash import Dash, dcc, html, Input, Output
from vivendi_data import VivendiStock

app_data = VivendiStock()
app_pages = {
    '/': html.Div([
        html.Div(className='container', children=[
            html.Hr(className='seperator'),
            html.Div(className='row', children=[
                html.Div(className='col-sm-12', children=[
                    html.Form(children=[
                        html.Fieldset(children=[
                            html.Div(className='form-group', children=[
                                html.Label(children='Shares amount'),
                                dcc.Slider(id='amount',
                                           min=1, max=4, value=2,
                                           marks={i: f'{i*500}' for i in range(1, 5)}
                                           ),
                            ])
                        ])
                    ])
                ])
            ]),
            html.Div(className='row', children=[
                html.Div(className='col-sm-12', children=[
                    html.Div(id='output_graph')
                ])
            ])
        ])
    ]),
}


def get_company_graph(key):
    name = app_data.name(key)
    current_price = app_data.current_price(key)
    highest_price = app_data.high_day_price(key)
    lowest_price = app_data.low_day_price(key)

    change_percent = app_data.price_change(key)
    if change_percent > 0:
        change_percent = f'+{change_percent}%'
        change_color = 'success'
    else:
        change_percent = f'{change_percent}%'
        change_color = 'danger'

    return html.Div(className='row', children=[
        html.Div(className='col-sm-10', children=[
            dcc.Graph(id=f'stocks_graph_{key}', figure={
                'data': [{'x': app_data.index(), 'y': app_data.price(key), 'type': 'line', 'name': key}],
                'layout': {'title': f'{name} ({key})'}
            })
        ]),
        html.Div(className='col-sm-2', children=[
            html.Div(className='container top-margin', children=[
                html.Div(className='row', children=[
                    html.Div(className='col-sm-10', children=[
                        html.H2(className='text-right', children=[current_price])
                    ]),
                    html.Div(className='col-sm-2', children=[
                        html.H6(className=f'text-left text-{change_color}', children=[change_percent])])
                ])
            ])
        ])
    ])


# define the app
app = Dash('Stock tracker')
app.css.config.serve_locally = False
app.css.append_css({'external_url': './static/stylesheets/bootstrap.css'})
app.css.append_css({'external_url': './static/stylesheets/styles.css'})

app.config['suppress_callback_exceptions'] = True
app.layout = html.Div(children=[
    dcc.Location(id='url', refresh=False),
    html.H3(className='center-align big-Close', children='Vivendi Group Stock Value Tracker'),
    html.Div(id='page-content')
])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    try:
        return app_pages[pathname]
    except:
        return app_pages['/']


@app.callback(Output(component_id='output_graph', component_property='children'),
              [Input(component_id='amount', component_property='value')])
def update_graph(amount_data):
    try:
        rows = []
        for sid in app_data.keys():
            rows.append(html.Hr(className='seperator'))
            rows.append(get_company_graph(sid))
        return html.Div(className='container', children=rows)

    except Exception as e:
        print(f'Exception: {e}')
        time.sleep(1)


if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=True)
