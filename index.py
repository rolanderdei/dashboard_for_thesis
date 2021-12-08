# Standard libaries for DataFrame, Dtypes & I/O
import numpy as np
import pandas as pd

# Datetime
from datetime import datetime
from datetime import date

# Plotting
import plotly.express as px
import plotly.graph_objects as go

# PostgreSQL
import psycopg2

# Pickle
import pickle

# Sklearn - for polinomial transformation
from sklearn.preprocessing import PolynomialFeatures

# Dash
import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html

from my_config import host_name, port, database_name, username, pw

# Query for the whole database
query = '''SELECT group_name, AVG(metrics.du_disk_usage_value) AS du_disk_usage_value, AVG(metrics.nd_cg_cpu_visibletotal_value) AS nd_cg_cpu_visibletotal_value, AVG(metrics.nd_cg_mem_visibletotal_value) AS nd_cg_mem_visibletotal_value, AVG(metrics.nd_cg_net_eth0_received_value) AS nd_cg_net_eth0_received_value, AVG(metrics.nd_cg_net_eth0_sent_value) AS nd_cg_net_eth0_sent_value, AVG(metrics.nd_cg_net_eth0_visibletotal_value) AS nd_cg_net_eth0_visibletotal_value, parameters.application_instances_value, parameters.application_case_value, parameters.application_metric_count_value, parameters.application_labels_value, parameters.cortex_number_of_nginx_value, parameters.cortex_number_of_distributor_value, parameters.cortex_number_of_ingester_value, parameters.cortex_blocks_storage_tsdb_block_ranges_period_value, parameters.cortex_blocks_storage_tsdb_retention_period_value, parameters.cortex_blocks_storage_tsdb_wal_compression_value, parameters.cortex_compactor_blocks_ranges_value
FROM metrics INNER JOIN parameters ON metrics.timestamp=parameters.timestamp
WHERE (parameters.prometheus_remote_write_max_samples_per_send_value IS NULL OR parameters.prometheus_remote_write_max_samples_per_send_value = 100) AND metrics.group_name IN ('cortex compactor', 'cortex distributor', 'cortex ingester', 'cortex nginx', 'minio', 'prometheus server')
GROUP BY metrics.group_name, parameters.application_instances_value, parameters.application_case_value, parameters.application_metric_count_value, parameters.application_labels_value, parameters.cortex_number_of_nginx_value, parameters.cortex_number_of_distributor_value, parameters.cortex_number_of_ingester_value, parameters.cortex_blocks_storage_tsdb_block_ranges_period_value, parameters.cortex_blocks_storage_tsdb_retention_period_value, parameters.cortex_blocks_storage_tsdb_wal_compression_value, parameters.cortex_compactor_blocks_ranges_value
'''

# X and Y axis dictionary with unit names
axis_dictionary = {
    "application_labels_value": "Number of labels",
    "application_metric_count_value": "Number of time series",
    "application_instances_value": "Number of applications",
    "application_case_value": "Type of metrics",
    "group_name": "Application's group",
    "instance": "Application instance",
    "du_disk_usage_value": "Disk Usage (MB)",
    "nd_cg_cpu_visibletotal_value": "CPU (%)",
    "nd_cg_mem_visibletotal_value": "Memory (MiB)",
    "nd_cg_net_eth0_received_value": "Network - Received (kilobit/s)",
    "nd_cg_net_eth0_sent_value": "Network - Sent (kilobit/s)",
    "nd_cg_net_eth0_visibletotal_value": "Network - Total (kilobit/s)",
    "cortex_number_of_nginx_value": "Number of Nginx",
    "cortex_number_of_distributor_value": "Number of Distributors",
    "cortex_number_of_ingester_value": "Number of Ingesters",
    "cortex_blocks_storage_tsdb_retention_period_value": "TSDB Retention Period",
    "cortex_blocks_storage_tsdb_wal_compression_value": "TSDB WAL compression",
    "cortex_compactor_blocks_ranges_value": "TSDB Compactor Block"
}

# SQL query - parameters, metrics table
def sql_queries(query):

    # Connecting to the PostgreSQL server
    connect = psycopg2.connect(host=host_name, port=port, database=database_name, user=username, password=pw)

    read_data = pd.read_sql_query(query, con=connect)
    
    # Closing connection
    connect.close()
    
    return read_data

# Bar plot creation:
def create_bar_plot(plot_data, color, y_axis):
    try:
        # Mean calculation
        plot_data = plot_data.groupby(['group_name', color]).mean()
        plot_data = plot_data.reset_index()

        # Delete N/A values
        plot_data = plot_data[plot_data[color].notna()]
        plot_data = plot_data[plot_data[y_axis].notna()]

        # Sorting for visualisation
        plot_data = plot_data.sort_values(by=[color, 'group_name'])

        plot_data[color] = plot_data[color].astype("category")

        # Creating plotting area
        fig = px.bar(plot_data, y=y_axis, x='group_name', color=color, barmode="group", hover_name=color,
                labels={color: axis_dictionary[color], y_axis: axis_dictionary[y_axis], 'group_name': axis_dictionary['group_name']}, 
                template="simple_white",
                color_discrete_sequence=px.colors.qualitative.G10
        )
        fig.update_layout(legend_font={"size": 14}, font_size=14)
        fig.update_yaxes(linewidth=2, linecolor='black', title_font = {"size": 16}, showgrid=True)
        fig.update_xaxes(linewidth=2, linecolor='black', title_font = {"size": 16}, type='category', categoryorder='category ascending')

    except:
        # If there is no data to display replace plot with the text 'No Data to Display'
        fig = go.Figure().add_annotation(x=3.5, y=2.5, text="No Data to Display", font=dict(family="sans serif", size=25, color="crimson"), showarrow=False, yshift=10)
    
    fig.update_layout(height=500, width=1850)

    return fig

# Filtering plot data, using the filter fields, blocking X axis
def filtering(data, x_axis, application_labels, metric_count_series, application_case_series, nginx, distributor, ingester, tsdb_compactor_blocks_ranges, tsdb_retention_period, tsdb_wal_compression, tsdb_block_ranges_period):

    # Create plot dataframe from the original one
    plot_data = data

    if (len(application_labels) != 0 and x_axis != 'application_labels_value'):
        plot_data = plot_data[plot_data.application_labels_value.isin(application_labels)]

    if (len(metric_count_series) != 0 and x_axis != 'application_metric_count_value'):
        plot_data = plot_data[plot_data.application_metric_count_value.isin(metric_count_series)]

    if (len(application_case_series) != 0 and x_axis != 'application_case_value'):
        plot_data = plot_data[plot_data.application_case_value.isin(application_case_series)]

    if (len(nginx) != 0 and x_axis != 'cortex_number_of_nginx_value'):
        plot_data = plot_data[plot_data.cortex_number_of_nginx_value.isin(nginx)]

    if (len(distributor) != 0 and x_axis != 'cortex_number_of_distributor_value'):
        plot_data = plot_data[plot_data.cortex_number_of_distributor_value.isin(distributor)] 

    if (len(ingester) != 0 and x_axis != 'cortex_number_of_ingester_value'):
        plot_data = plot_data[plot_data.cortex_number_of_ingester_value.isin(ingester)]

    if (len(tsdb_compactor_blocks_ranges) != 0 and x_axis != 'cortex_compactor_blocks_ranges_value'):
        plot_data = plot_data[plot_data.cortex_compactor_blocks_ranges_value.isin(tsdb_compactor_blocks_ranges)]

    if (len(tsdb_retention_period) != 0 and x_axis != 'cortex_blocks_storage_tsdb_retention_period_value'):
        plot_data = plot_data[plot_data.cortex_blocks_storage_tsdb_retention_period_value.isin(tsdb_retention_period)] 

    if (len(tsdb_wal_compression) != 0 and x_axis != 'cortex_blocks_storage_tsdb_wal_compression_value'):
        plot_data = plot_data[plot_data.cortex_blocks_storage_tsdb_wal_compression_value.isin(tsdb_wal_compression)]

    if (len(tsdb_block_ranges_period) != 0 and x_axis != 'cortex_blocks_storage_tsdb_block_ranges_period_value'):
        plot_data = plot_data[plot_data.cortex_blocks_storage_tsdb_block_ranges_period_value.isin(tsdb_block_ranges_period)] 

    return plot_data
    
# INIT
# Pulling data
data = sql_queries(query)

# Filters sorting and value creating
# Categorical data casting
data['application_metric_count_value'] = data['application_metric_count_value'].astype("category")
data['application_labels_value'] = data['application_labels_value'].astype(int)
data['application_labels_value'] = data['application_labels_value'].astype("category")

application_labels = sorted(set(data['application_labels_value']))
metric_count = sorted(set(data['application_metric_count_value']))
application_case = sorted(set(data['application_case_value']))
number_of_nginx = sorted(set(data['cortex_number_of_nginx_value'].drop_duplicates()))
number_of_distributor = sorted(set(data['cortex_number_of_distributor_value'].drop_duplicates()))
number_of_ingester = sorted(set(data['cortex_number_of_ingester_value'].drop_duplicates()))
tsdb_block_ranges_period = sorted(set(data['cortex_blocks_storage_tsdb_block_ranges_period_value'].drop_duplicates()))
tsdb_retention_period = sorted(set(data['cortex_blocks_storage_tsdb_retention_period_value'].drop_duplicates()))
compactor_blocks_ranges = sorted(set(data['cortex_compactor_blocks_ranges_value'].drop_duplicates()))

# Sorting data by application name
data = data.sort_values(by=['group_name'])

# Importing models
linear_regression_nd_cg_cpu_visibletotal_value_cortex_distributor_model = pickle.load(open('linear_regression_nd_cg_cpu_visibletotal_value_cortex_distributor', 'rb'))
linear_regression_nd_cg_cpu_visibletotal_value_cortex_ingester_model = pickle.load(open('linear_regression_nd_cg_cpu_visibletotal_value_cortex_ingester', 'rb'))
linear_regression_nd_cg_cpu_visibletotal_value_prometheus_server_model = pickle.load(open('linear_regression_nd_cg_cpu_visibletotal_value_prometheus_server', 'rb'))

linear_regression_nd_cg_mem_usage_visibletotal_value_cortex_ingester_model = pickle.load(open('linear_regression_nd_cg_mem_usage_visibletotal_value_cortex_ingester', 'rb'))
linear_regression_nd_cg_mem_usage_visibletotal_value_prometheus_server_model = pickle.load(open('linear_regression_nd_cg_mem_usage_visibletotal_value_prometheus_server', 'rb'))

linear_regression_nd_cg_net_eth0_visibletotal_value_cortex_distributor_model = pickle.load(open('linear_regression_nd_cg_net_eth0_visibletotal_value_cortex_distributor', 'rb'))
linear_regression_nd_cg_net_eth0_visibletotal_value_cortex_ingester_model = pickle.load(open('linear_regression_nd_cg_net_eth0_visibletotal_value_cortex_ingester', 'rb'))
linear_regression_nd_cg_net_eth0_visibletotal_value_prometheus_server_model = pickle.load(open('linear_regression_nd_cg_net_eth0_visibletotal_value_prometheus_server', 'rb'))

# Create Dash app
app = dash.Dash()

# Create app layout
app.layout = html.Div(children=[

    #######################################################################################################
    #                                           Title                                                     #
    #######################################################################################################
    html.H2(
        children="Low Footprint Data Ingestion and Analytics 🖥️",
        style={'textAlign': 'center','font-size': '36px'}),

    #######################################################################################################
    #                                           Filter(s)                                                 #
    #######################################################################################################
    
    html.H2(
        children='Filters',
        style={'textAlign': 'center'}),

    # Number of time series drop down component
    html.Div(
        children=[
            html.Div(children="Number of time series"),
            dcc.Dropdown(id='metric_count_series-dropdown', options=[
                {'value': x, 'label': x} for x in metric_count
            ], multi=True, value=[30000]),
        ],
        style={'width': '33%',
               'display': 'inline-block',
               'fontSize': 18}),

    # Application labels drop down component
    html.Div(
        children=[
            html.Div(children="Number of labels"),
            dcc.Dropdown(id='application_labels-dropdown', options=[
                {'value': x, 'label': x} for x in application_labels
            ], multi=True, value=[20]),
        ],
        style={'width': '33%',
               'display': 'inline-block',
               'fontSize': 18}),

    # Application case drop down component
    html.Div(
        children=[
            html.Div(children="Type of metrics"),
            dcc.Dropdown(id='type_of_metrics-dropdown', options=[
                {'value': x, 'label': x} for x in application_case
            ], multi=True, value=['quasi_real']),
        ],
        style={'width': '33%',
               'display': 'inline-block',
               'fontSize': 18}),

    # Number of nginx drop down component
    html.Div(
        children=[
            html.Div(children="Number of nginx"),
            dcc.Dropdown(id='nginx-dropdown', options=[
                {'value': x, 'label': x} for x in number_of_nginx 
            ], multi=True, value=[1]),
        ],
        style={'width': '33%',
               'display': 'inline-block',
               'fontSize': 18}),

    # Retention period drop down component
    html.Div(
        children=[
            html.Div(children="Number of distributor"),
            dcc.Dropdown(id='distributor-dropdown', options=[
                {'value': x, 'label': x} for x in number_of_distributor
            ], multi=True, value=[1]),
        ],
        style={'width': '33%',
               'display': 'inline-block',
               'fontSize': 18}),

    # Retention period drop down component
    html.Div(
        children=[
            html.Div(children="Number of ingester"),
            dcc.Dropdown(id='ingester-dropdown', options=[
                {'value': x, 'label': x} for x in number_of_ingester
            ], multi=True, value=[2]),
        ],
        style={'width': '33%',
               'display': 'inline-block',
               'fontSize': 18}),

    # Compactor Blocks Ranges drop down component
    html.Div(
        children=[
            html.Div(children="Compactor Blocks Ranges"),
            dcc.Dropdown(id='tsdb_compactor_blocks_ranges-dropdown', options=[
                {'value': x, 'label': x} for x in compactor_blocks_ranges
            ], multi=True, value=[]),
        ],
        style={'width': '33%',
               'display': 'inline-block',
               'fontSize': 18}),

    # TSDB Retention Period drop down component
    html.Div(
        children=[
            html.Div(children="TSDB Retention Period"),
            dcc.Dropdown(id='tsdb_retention_period-dropdown', options=[
                {'value': x, 'label': x} for x in tsdb_retention_period
            ], multi=True, value=[21600]),
        ],
        style={'width': '33%',
               'display': 'inline-block',
               'fontSize': 18}),

    # TSDB WAL compression drop down component
    html.Div(
        children=[
            html.Div(children="TSDB WAL compression"),
            dcc.Dropdown(id='tsdb_wal_compression-dropdown', options=[
                {'label': 'True', 'value': True},
                {'label': 'False', 'value': False},
            ], multi=True, value=[False]),
        ],
        style={'width': '33%',
               'display': 'inline-block',
               'fontSize': 18}),

    # TSDB Block Ranges Period drop down component
    html.Div(
        children=[
            html.Div(children="TSDB Block Ranges Period"),
            dcc.Dropdown(id='tsdb_block_ranges_period-dropdown', options=[
                {'value': x, 'label': x} for x in tsdb_block_ranges_period
            ], multi=True, value=[7200]),
        ],
        style={'width': '33%',
               'display': 'inline-block',
               'fontSize': 18}),
    
    # Placeholder
    html.Br(),
    html.Br(),
    html.Hr(),

    # X axis radio items
    html.Div(
        children=[
            html.H3(children="Comparative analysis"),
            dcc.RadioItems(
                id='x_axis-checklist',
                options=[
                    {'label': 'Number of time series ', 'value': 'application_metric_count_value'},
                    {'label': 'Number of labels ', 'value': 'application_labels_value'},
                    {'label': 'Type of metrics ', 'value': 'application_case_value'},
                    {'label': 'Number of Nginx ', 'value': 'cortex_number_of_nginx_value'},
                    {'label': 'Number of Distributors ', 'value': 'cortex_number_of_distributor_value'},
                    {'label': 'Number of Ingesters ', 'value': 'cortex_number_of_ingester_value'},
                    {'label': 'Compactor Blocks Ranges ', 'value': 'cortex_compactor_blocks_ranges_value'},
                    {'label': 'TSDB Retention Period ', 'value': 'cortex_blocks_storage_tsdb_retention_period_value'},
                    {'label': 'TSDB WAL compression ', 'value': 'cortex_blocks_storage_tsdb_wal_compression_value'},
                    {'label': 'TSDB Block Range Periods ', 'value': 'cortex_blocks_storage_tsdb_block_ranges_period_value'}
                ],
                value='cortex_blocks_storage_tsdb_wal_compression_value'
            ),
        ],
        style={'width': '100%',
            'textAlign': 'center',
            'fontSize': 17}),

    # Placeholder
    html.Br(), html.Br(),


    # Tabs component
    dcc.Tabs(children=[

        #######################################################################################################
        #                                           Tab: 1                                                    #
        #######################################################################################################
        dcc.Tab(label='CPU', children=[

            # Placeholder
            html.Br(),

            # Box or violin plot
            dcc.Graph(id="tab1_plot")
        ]),

        #######################################################################################################
        #                                           Tab: 2                                                    #
        #######################################################################################################
        dcc.Tab(label='Disk', children=[

            # Placeholder
            html.Br(),

            # Box or violin plot
            dcc.Graph(id="tab2_plot")
        ]),

        #######################################################################################################
        #                                           Tab: 3                                                    #
        #######################################################################################################
        dcc.Tab(label='Memory', children=[
            
            # Placeholder
            html.Br(),

            # Box or violin plot
            dcc.Graph(id="tab3_plot")
        ]),

        #######################################################################################################
        #                                           Tab: 4                                                   #
        #######################################################################################################
        dcc.Tab(label='Network', children=[
            
            # Placeholder
            html.Br(),

            # Y axis radio items
            html.Div(
                children=[
                    html.H2(children="Y axis"),
                    dcc.RadioItems(
                        id='y_axis-checklist4',
                        options=[
                            {'label': 'Network - Received', 'value': 'nd_cg_net_eth0_received_value'},
                            {'label': 'Network - Sent', 'value': 'nd_cg_net_eth0_sent_value'},
                            {'label': 'Network - Total', 'value': 'nd_cg_net_eth0_visibletotal_value'}
                        ],
                        value='nd_cg_net_eth0_visibletotal_value'
                    ),
                ],
                style={'width': '100%',
                    'display': 'inline-block', 'textAlign': 'center',
                    'fontSize': 18}),
            
            # Placeholder
            html.Br(),
            html.Br(),


            # Box or violin plot
            dcc.Graph(id="tab4_plot"),

        ]),

        #######################################################################################################
        #                                           Tab: 5                                                    #
        #######################################################################################################
        dcc.Tab(label='Linear regression models', children=[

            html.Div(children=[
                html.H2(children="Estimators for Prometheus server, Cortex Ingester, Cortex Distributor and Minio")
            ],
                style={'textAlign': 'center'}),

            html.Div(children=[
                html.H2(children="Inputs"),
            ],
                style={'textAlign': 'center'}),
                
        
            html.Div(children=[
                html.H3(children="Number of time series"),
                dcc.Input(
                    id="application_metric_count_value-input",
                    type="number",
                    placeholder="Range: 3,000-200,000",
                    value=300000,
                    min=0,
                ),
            ],
            style={'width': '20%',
                'display': 'inline-block', 'textAlign': 'center', 'fontSize': 18}),

            html.Div(children=[
                html.H3(children="Number of labels"),  
                dcc.Input(
                    id="application_labels_value-input",
                    type="number",
                    placeholder="Range: 5-30",
                    value=20,
                    min=5, max=30,
                ),
            ],
            style={'width': '20%',
                'display': 'inline-block', 'textAlign': 'center', 'fontSize': 18}),

            html.Div(children=[
                html.H3(children="Prometheus WAL Compression"),
                dcc.Input(
                    id="prometheus_wal_compression_value-input",
                    type="number",
                    value=0,
                    placeholder="True - 1 or False - 0",
                    min=0, max=1,
                ),
            ],
            style={'width': '20%',
                'display': 'inline-block', 'textAlign': 'center', 'fontSize': 18}),

            html.Div(children=[    
                html.H3(children="Number of Nginx"),
                dcc.Input(
                    id="number_of_nginx-input",
                    type="number",
                    placeholder="Range: 0-5",
                    value=1,
                    min=0, max=5,
                ),
            ],
            style={'width': '20%',
                'display': 'inline-block', 'textAlign': 'center', 'fontSize': 18}),

            html.Div(children=[    
                html.H3(children="Number of Distributors"),
                dcc.Input(
                    id="number_of_distributor-input",
                    type="number",
                    placeholder="Range: 0-5",
                    value=1,
                    min=0, max=5,
                ),
            ],
            style={'width': '20%',
                'display': 'inline-block', 'textAlign': 'center', 'fontSize': 18}),

            html.Div(children=[    
                html.H3(children="Number of Ingesters"),
                dcc.Input(
                    id="number_of_ingester-input",
                    type="number",
                    placeholder="Range: 0-10",
                    value=2,
                    min=0, max=10,
                ),
            ],
            style={'width': '20%',
                'display': 'inline-block', 'textAlign': 'center', 'fontSize': 18}),

            html.Div(children=[ 
                html.H3(children="TSDB Retention Period"), 
                dcc.Input(
                    id="tsdb_retention_period-input",
                    type="number",
                    placeholder="Range: 3600-216,000",
                    value=21600,
                    min=3600, max=216000,
                ),
            ],
            style={'width': '20%',
                'display': 'inline-block', 'textAlign': 'center', 'fontSize': 18}),   

            html.Div(children=[ 
                html.H3(children="TSDB WAL compression"), 
                dcc.Input(
                    id="tsdb_wal_compression-input",
                    type="number",
                    placeholder="True - 1 or False - 0",
                    min=0, max=1,
                ),
            ],
            style={'width': '20%',
                'display': 'inline-block', 'textAlign': 'center', 'fontSize': 18}),   

            html.Div(children=[ 
                html.H3(children="TSDB Block Ranges Period"), 
                dcc.Input(
                    id="tsdb_block_ranges_period-input",
                    type="number",
                    placeholder="Range: 1,000-72,000",
                    value=7200,
                    min=1500, max=72000,
                ),
            ],
            style={'width': '20%',
                'display': 'inline-block', 'textAlign': 'center', 'fontSize': 18}),         

            # Placeholder
            html.Br(),
            html.Br(),
            html.Br(),
            html.Hr(),

            # Results
            html.Div(children=[
                html.H2(children="Results come from linear regression models based on our measurements"),
                html.H2(children="Results"),

                # CPU outputs
                html.H2(children="CPU"),
                html.Div(id='distributor_cpu-output'),
                html.Div(id='ingester_cpu-output'),
                html.Div(id='prometheus_cpu-output'),

                # Placeholder
                html.Br(),
                html.Br(),

                # Disk outputs
                html.H2(children="Disk"),
                html.Div(id='ingester_disk-output'),
                html.Div(id='minio_disk-output'),
                html.Div(id='prometheus_disk-output'),

                html.Div(children=[
                    html.H4(children="Cumulative value (8 hours)"),
                ],
                style={'textAlign': 'center'}),

                # Placeholder
                html.Br(),

                # Memory outputs
                html.H2(children="Memory"),
                html.Div(id='ingester_memory-output'),
                html.Div(id='prometheus_memory-output'),

                # Placeholder
                html.Br(),
                html.Br(),

                # Network outputs
                html.H2(children="Network"),
                html.Div(id='distributor_network-output'),
                html.Div(id='ingester_network-output'),
                html.Div(id='prometheus_network-output'),

                # Placeholder
                html.Br(),
                html.Br(),
            ],
            style={'width': '100%', 'textAlign': 'center', 'fontSize': 19}), 
        ])
    ])
])

@app.callback(
    [
        Output(component_id='tab1_plot', component_property='figure'),
        Output(component_id='tab2_plot', component_property='figure'),
        Output(component_id='tab3_plot', component_property='figure'),
        Output(component_id='tab4_plot', component_property='figure')
    ],
    [
        Input(component_id='x_axis-checklist', component_property='value'),
        Input(component_id='y_axis-checklist4', component_property='value'),
        Input(component_id='application_labels-dropdown', component_property='value'),
        Input(component_id='metric_count_series-dropdown', component_property='value'),
        Input(component_id='type_of_metrics-dropdown', component_property='value'),
        Input(component_id='tsdb_retention_period-dropdown', component_property='value'),
        Input(component_id='nginx-dropdown', component_property='value'),
        Input(component_id='distributor-dropdown', component_property='value'),
        Input(component_id='ingester-dropdown', component_property='value'),
        Input(component_id='tsdb_compactor_blocks_ranges-dropdown', component_property='value'),
        Input(component_id='tsdb_wal_compression-dropdown', component_property='value'),
        Input(component_id='tsdb_block_ranges_period-dropdown', component_property='value')
    ]
)
def refresh_plots(x_axis, y_axis4, application_labels, metric_count_series, application_case_series, tsdb_retention_period, nginx, distributor, ingester, tsdb_compactor_blocks_ranges, tsdb_wal_compression, tsdb_block_ranges_period):

    #### Filtering ####
    plot_data = filtering(data, x_axis, application_labels, metric_count_series, application_case_series, nginx, distributor, ingester, tsdb_compactor_blocks_ranges, tsdb_retention_period, tsdb_wal_compression, tsdb_block_ranges_period)

    y_axis1 = 'nd_cg_cpu_visibletotal_value'
    y_axis2 = 'du_disk_usage_value'
    y_axis3 = 'nd_cg_mem_visibletotal_value'

    ####  Ploting  ####
    fig1 = create_bar_plot(plot_data, x_axis, y_axis1)
    fig2 = create_bar_plot(plot_data, x_axis, y_axis2)
    fig3 = create_bar_plot(plot_data, x_axis, y_axis3)
    fig4 = create_bar_plot(plot_data, x_axis, y_axis4)

    return fig1, fig2, fig3, fig4

@app.callback(
    [
        Output(component_id='distributor_cpu-output', component_property='children'),
        Output(component_id='ingester_cpu-output', component_property='children'),
        Output(component_id='prometheus_cpu-output', component_property='children'),
        Output(component_id='ingester_disk-output', component_property='children'),
        Output(component_id='minio_disk-output', component_property='children'),
        Output(component_id='prometheus_disk-output', component_property='children'),
        Output(component_id='ingester_memory-output', component_property='children'),
        Output(component_id='prometheus_memory-output', component_property='children'),
        Output(component_id='distributor_network-output', component_property='children'),
        Output(component_id='ingester_network-output', component_property='children'),
        Output(component_id='prometheus_network-output', component_property='children')
    ],
    [
        Input(component_id='prometheus_wal_compression_value-input', component_property='value'),
        Input(component_id='application_metric_count_value-input', component_property='value'),
        Input(component_id='application_labels_value-input', component_property='value'),
        Input(component_id='number_of_nginx-input', component_property='value'),
        Input(component_id='number_of_distributor-input', component_property='value'),
        Input(component_id='number_of_ingester-input', component_property='value'),
        Input(component_id='tsdb_wal_compression-input', component_property='value'),
        Input(component_id='tsdb_retention_period-input', component_property='value'),
        Input(component_id='tsdb_block_ranges_period-input', component_property='value')
    ]
)
def linear_regression_calculation(prometheus_wal_compression, application_metric_count, application_labels, number_of_nginx, number_of_distributor, number_of_ingester, tsdb_wal_compression, tsdb_retention_period, tsdb_block_ranges_period):

    if (prometheus_wal_compression == None or  application_metric_count == None or  application_labels == None or  number_of_nginx == None or  number_of_distributor == None or  number_of_ingester == None or tsdb_wal_compression == None or tsdb_retention_period == None or tsdb_block_ranges_period == None):

        return "Waiting for user input", None, None, "Waiting for user input", None, None, "Waiting for user input", None, "Waiting for user input", None, None

    Xnew = [[prometheus_wal_compression, application_metric_count, application_labels, number_of_nginx, number_of_distributor, number_of_ingester, tsdb_block_ranges_period, tsdb_retention_period, tsdb_wal_compression]]

    Xnew_disk = [[application_metric_count]]

    # CPU
    distributor_cpu = 'Distributor: ' + str(round(linear_regression_nd_cg_cpu_visibletotal_value_cortex_distributor_model.predict(Xnew)[0])) + ' %'
    ingester_cpu = 'Ingester: ' + str(round(linear_regression_nd_cg_cpu_visibletotal_value_cortex_ingester_model.predict(Xnew)[0])) + ' %'
    prometheus_cpu = 'Prometheus: ' + str(round(linear_regression_nd_cg_cpu_visibletotal_value_prometheus_server_model.predict(Xnew)[0])) + ' %'

    # Disk
    ingester_disk = 'Ingester: ' + str(round(0.0032 * application_metric_count + 385.74207)) + ' MB'
    minio_disk = 'Minio: ' + str(round(0.003528 * application_metric_count + 251.671882)) + ' MB'
    prometheus_disk = 'Prometheus: ' + str(round(0.00496 * application_metric_count - 220.372656)) + ' MB'

    # Memory
    ingester_memory = 'Ingester: ' + str(round(linear_regression_nd_cg_mem_usage_visibletotal_value_cortex_ingester_model.predict(Xnew)[0])) + ' MiB'
    prometheus_memory = 'Prometheus: ' + str(round(linear_regression_nd_cg_mem_usage_visibletotal_value_prometheus_server_model.predict(Xnew)[0])) + ' MiB'

    # Network
    distributor_network = 'Distributor: ' + str(round(linear_regression_nd_cg_net_eth0_visibletotal_value_cortex_distributor_model.predict(Xnew)[0])) + ' kilobit/s'
    ingester_network = 'Ingester: ' + str(round(linear_regression_nd_cg_net_eth0_visibletotal_value_cortex_ingester_model.predict(Xnew)[0])) + ' kilobit/s'
    prometheus_network = 'Prometheus: ' + str(round(linear_regression_nd_cg_net_eth0_visibletotal_value_prometheus_server_model.predict(Xnew)[0])) + ' kilobit/s'

    return distributor_cpu, ingester_cpu, prometheus_cpu, ingester_disk, minio_disk, prometheus_disk, ingester_memory, prometheus_memory, distributor_network, ingester_network, prometheus_network
    
if __name__ == '__main__':
    app.run_server(host='0.0.0.0', debug=False)                                                                            