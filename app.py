from dash import Dash, dcc, html, Input, Output
from vivendi_data import VivendiStock, STOCK

app_data = VivendiStock()


def get_graph(key, name):
    history, current_price, change_percent = app_data.get_data(key)

    if change_percent > 0:
        change_percent = f'+{change_percent}%'
        change_color = 'success'
    else:
        change_percent = f'{change_percent}%'
        change_color = 'danger'

    return html.Div(className='row', children=[
        html.Div(className='col-sm-10', children=[
            dcc.Graph(id=f'stocks_graph_{key}', figure={
                'data': [{'x': history.index, 'y': history, 'type': 'line', 'name': key}],
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

graphs = [get_graph('AUD.VALUE', 'Estimated value in AUD')]
graphs += [get_graph(stock, STOCK[stock]['name']) for stock in STOCK]

app.layout = html.Div(children=[
    html.H3(className='center-align big-Close', children='Vivendi Group Stock Value Tracker'),
    html.Div(className='container', children=graphs)
])

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=True)
