
import sys
import os.path
import csv
import threading
from pathlib import Path
import random
from time import time
from termcolor import colored
from bokeh.layouts import column
import yaml
import numpy as np
import pandas as pd
import statistics as stats
from bokeh.server import session
from bokeh.util.token import generate_session_id
from bokeh.plotting import figure, show, curdoc
from bokeh.models import HoverTool, ColumnDataSource, LinearAxis, Range1d
from bokeh.models.formatters import TickFormatter
from bokeh.io import output_file, show
from flask import Flask, render_template
from bokeh.client import pull_session
from bokeh.embed import server_session

# app = Flask(__name__)

# @app.route('/', methods=['GET'])
# def bkapp_page():
#     # Connect to a Bokeh server session
#     with pull_session(url="http://localhost:5006/plotter") as session:
#         # Customize the session (e.g., update the plot title)
#         session.document.roots.children[0].title.text = "Special sliders for a specific user!"

#         # Generate a script to load the customized session
#         script = server_session(session_id=session.id, url='http://localhost:5006/plotter')

#         # Render the template with the script
#         return render_template("embed.html", script=script, template="Flask")

BOKEH_COLORS = [ 
    'aqua',
    'aquamarine',
    'black',
    'blue',
    'blueviolet',
    'brown',
    'burlywood',
    'cadetblue',
    'chartreuse',
    'chocolate',
    'coral',
    'cornflowerblue',
    'crimson',
    'cyan',
    'darkblue',
    'darkcyan',
    'darkgolden,rod',
    'darkgray',
    'darkgreen',
    'darkgrey',
    'darkkhaki',
    'darkmagenta',
    'darkolivegreen',
    'darkorange',
    'darkorchid',
    'darkred',
    'darksalmon',
    'darkseagreen',
    'darkslateblue',
    'darkslategray',
    'darkslategrey',
    'darkturquoise',
    'darkviolet',
    'deeppink',
    'deepskyblue',
    'dimgray',
    'dimgrey',
    'dodgerblue',
    'firebrick',
    'forestgreen',
    'fuchsia',
    'gainsboro',
    'gold',
    'goldenrod',
    'gray',
    'green',
    'greenyellow',
    'grey',
    'hotpink',
    'indianred',
    'indigo',
    'khaki',
    'lawngreen',
    'lightblue',
    'lightcoral',
    'lightcyan',
    'lightgray',
    'lightgreen',
    'lightgrey',
    'lightpink',
    'lightsalmon',
    'lightseagreen',
    'lightskyblue',
    'lightslategray',
    'lightslategrey',
    'lightsteelblue'
    'lime',
    'limegreen',
    'magenta',
    'maroon',
    'mediumaquamarine',
    'mediumblue',
    'mediumorchid',
    'mediumpurple',
    'mediumseagreen',
    'mediumslateblue',
    'mediumspringgreen',
    'mediumturquoise',
    'mediumvioletred',
    'midnightblue',
    'navy',
    'olive',
    'olivedrab',
    'orange',
    'orangered',
    'orchid',
    'palegreen',
    'paleturquoise',
    'palevioletred',
    'peachpuff',
    'peru',
    'pink',
    'plum',
    'powderblue',
    'purple',
    'rebeccapurple',
    'red',
    'rosybrown',
    'royalblue',
    'saddlebrown',
    'salmon',
    'sandybrown',
    'seagreen',
    'sienna',
    'silver',
    'skyblue',
    'slateblue',
    'slategray',
    'slategrey',
    'springgreen',
    'steelblue',
    'tan',
    'teal',
    'thistle',
    'tomato',
    'turquoise',
    'violet',
    'yellow',
    'yellowgreen'
    ]

COLOURS_LENGTH = len(BOKEH_COLORS)


# DEFAULTS
DEFAULT_PLOT_HEIGHT = 600
DEFAULT_PLOT_WIDTH = 1800

DEFAULT_TOOLTIPS = [
    ("x, y", "$x, $y "),
    ("index", "$index")   
] 

## Error Codes
SUCCESSFUL = 0
FILE_NOT_FOUND = 1
COL_NOT_FOUND = 2
FAILED_TO_LOAD_DATA = 3 
INVALID_CONFIG_FILE = 4


class Plot():
    
    def __init__(self, plot: dict):
        self._df = None
        self._data_path = plot['data_path']
        
        self.plot_name = plot['plot_name']

        self.indexs = None
        if plot.get('indexs', None) != None:
            if self._validate_indexs(plot.get('indexs', None)) == INVALID_CONFIG_FILE:
                exit(INVALID_CONFIG_FILE)
            self.indexs = plot.get('indexs', None)[0], plot.get('indexs', None)[1]

        self.x_datetime = plot['x_datetime']
        self.x_col_name = plot['x_col']
        self.y_col_names = plot['y_cols']
        self.units = plot.get('units', None)
        self.figure = None

        if (self._load_csv() != SUCCESSFUL) or (self._validate_columns() != SUCCESSFUL):
            return
        
        self.generate_plot()
        self._ranges = (0, 0, 0, 0)
        threading.Thread(target=self.update_thread, daemon=True).start()
        
        
    
    def _load_csv(self) -> int:
        if not os.path.exists(self._data_path):
            print(f"ERROR: The given path <{self._data_path}> for plot {self.plot_name} does not exist")
            return FILE_NOT_FOUND
        self._data_path = Path(self._data_path)
        self._df = pd.read_csv(self._data_path)

        if self.indexs != None:
            self._df = self._df.iloc[self.indexs[0]: self.indexs[1], :]
        
        return SUCCESSFUL


    def _validate_columns(self) -> int:
        
        for col_name in self.y_col_names:
            if col_name not in self._df:
                print(f"ERROR: Column <{col_name}> does not exist in csv {self._data_path}.")
                return COL_NOT_FOUND
            
        return SUCCESSFUL
    

    def _validate_indexs(self, indexs):
         for i in indexs:
            try:
                int(i)
            except ValueError:
                print(f"VALUE ERROR: Invalid Index. Correct config index format is: \r\n>> indexs: List<int, int>\r\nE.G.:\r\n>> indexs: [225, 290]")
                return INVALID_CONFIG_FILE


    """def generate_plot(self): 
        if self.x_datetime:
            custom_hover = HoverTool(
                tooltips = [
                    ('Time', "$x{%Y-%m-%d %H:%M:%S}"),
                    ('Y Val', '$y'),
                    ("index", "$index") 
                ],                
                mode = 'vline'
                )
            custom_hover.formatters = {
                    "$x": 'datetime', # use 'datetime' formatter 
                }
            
            self._df[self.x_col_name] = pd.to_datetime(self._df[self.x_col_name])
            self.figure = figure(x_axis_type='datetime',width=DEFAULT_PLOT_WIDTH, height=DEFAULT_PLOT_HEIGHT, title="\r\n\n" + self.plot_name)
            self.figure.title.align = "center"
            self.figure.title.text_font_size = "25px"

            self.figure.add_tools(custom_hover)
            
            
        else:
            self.figure = figure(width=DEFAULT_PLOT_WIDTH, height=DEFAULT_PLOT_HEIGHT, title=self.plot_name, tooltips=DEFAULT_TOOLTIPS)
        
        # For multiple y columns
        columns = {self.x_col_name : self._df[self.x_col_name]}
        for y_col in self.y_col_names:
            # rand_color = BOKEH_COLORS[random.randint(0, COLOURS_LENGTH - 1)]
            # self.figure.scatter(x=self._df[self.x_col_name], y=self._df[y_col], size=4, legend_label = y_col, color=rand_color)

            columns.update({y_col : self._df[y_col]})
        self.data_source = ColumnDataSource(data = columns)

        for y_col in self.y_col_names:
            rand_color = BOKEH_COLORS[random.randint(0, COLOURS_LENGTH - 1)]
            self.figure.scatter(x=self.x_col_name, y=y_col, size=4, line_color=rand_color, source=self.data_source, legend_label=y_col)
   
        self.figure.xgrid.grid_line_color = 'navy'"""

    def rescale_y_axis(self):
        y_values = []
        for y_col in self.y_col_names:
            y_values.extend(self.data_source.data[y_col])
        if y_values:
            self.figure.y_range.start = min(y_values) - (max(y_values) - min(y_values))*0.4
            self.figure.y_range.end = max(y_values) + (max(y_values) - min(y_values))*0.4

    def rescale_x_axis(self):
        x_values = []
        for x_col in [self.x_col_name]:
            x_values.extend(self.data_source.data[x_col])
        if x_values:
            self.figure.x_range.start = min(x_values)
            self.figure.x_range.end = max(x_values)

    def generate_plot(self): 
        import time
        if self.x_datetime:
            custom_hover = HoverTool(
                tooltips = [
                    ('Time', "$x{%Y-%m-%d %H:%M:%S}"),
                    ('Y Val', '$y'),
                    ("index", "$index") 
                ],                
                mode = 'vline'
                )
            custom_hover.formatters = {
                    "$x": 'datetime', # use 'datetime' formatter 
                }
            
            self._df[self.x_col_name] = pd.to_datetime(self._df[self.x_col_name])
            self.figure = figure(x_axis_type='datetime',width=DEFAULT_PLOT_WIDTH, height=DEFAULT_PLOT_HEIGHT, title="\r\n\n" + self.plot_name)
            self.figure.title.align = "center"
            self.figure.title.text_font_size = "25px"

            self.figure.add_tools(custom_hover)

        else:
            custom_hover = HoverTool(
                tooltips = [
                    ('Y Val', '$y'),
                    ("index", "$index") 
                ],                
                mode = 'vline'
                )
            self.figure = figure(width=DEFAULT_PLOT_WIDTH, height=DEFAULT_PLOT_HEIGHT, title="\r\n\n" + self.plot_name)
            self.figure.title.align = "center"
            self.figure.title.text_font_size = "25px"

            self.figure.add_tools(custom_hover)
            
        # For multiple y columns
        columns = {self.x_col_name : self._df[self.x_col_name]}
        for y_col in self.y_col_names:
            columns.update({y_col : self._df[y_col]})

        self.data_source = ColumnDataSource(data = columns)
        # print(f"Enumeration: {list(enumerate(self.y_col_names))}")
        
        for i, y in enumerate(self.y_col_names):
            rand_color = BOKEH_COLORS[random.randint(0, COLOURS_LENGTH - 1)]
            
            # self.figure.scatter(self.x_col_name, y, source=self.data_source, size=4, color=rand_color, legend_label=y)
            if i > 0: # Additional axis on right of the plot for multiple y columns
                s = min(self._df[y]) - (max(self._df[y]) - min(self._df[y]))*0.4
                e = max(self._df[y]) + (max(self._df[y]) - min(self._df[y]))*0.4
                self.figure.extra_y_ranges.update({y: Range1d(start=s, end=e)})
                # time.sleep(0.1) 

                units = y # Default to column name as units if not specified in config
                if self.units != None:
                    #TODO: validate length of units list in config file matches number of y columns
                    units = self.units[i] if i < len(self.units) else y # Just in case length mismatch between y columns and units list in config

                self.figure.add_layout(LinearAxis(y_range_name=y, axis_label=units), 'right')
                self.figure.scatter(self.x_col_name, y, y_range_name=y,source=self.data_source, size=4, color=rand_color, legend_label=y)
            else:
                self.figure.scatter(self.x_col_name, y, source=self.data_source, size=4, color=rand_color, legend_label=y)
                units = y # Default to column name as units if not specified in config
                if self.units != None and len(self.units) > 0:
                    units = self.units[0]
                self.figure.yaxis.axis_label = units

            
            
        self.figure.legend.click_policy = "hide"
        self.figure.xgrid.grid_line_color = 'navy'



    ## CHAT Thread Version
    def update_thread(self):
        import time
        """Background thread that watches the CSV and updates the source."""
        # Wait for file to exist
        while not self._data_path.exists():
            time.sleep(1)
        print(f"{self.plot_name}: Starting update thread, watching {self._data_path} for new data...")
        with open(self._data_path, "r") as f:
            reader = csv.DictReader(f)
            index = 0

            for row in reader:
                # Skip existing rows (start plotting new data only)
                index += 1

            # Start reading new rows
            while True:
                line = f.readline()
                if not line:
                    time.sleep(1)
                    continue
                try:
                    row = next(csv.DictReader([line], fieldnames=reader.fieldnames))
                    # print(f"{self.plot_name}: Read new line: {row}")
                    index += 1
                    new_data = {self.x_col_name: [index]}
                    for y in self.y_col_names:
                        new_data[y] = [float(row[y])]
                except Exception:
                    continue

                # Thread-safe update
                # print(f"{self.plot_name}: New data - {new_data}")
                curdoc().add_next_tick_callback(lambda d=new_data, s=self.data_source: s.stream(d))
                # curdoc().add_next_tick_callback(lambda: print(f"{self.plot_name}: Updated source: {self.data_source.data}"))
                # curdoc().add_next_tick_callback(self.rescale_x_axis)
                # curdoc().add_next_tick_callback(self.rescale_y_axis)
                # curdoc().add_next_tick_callback(
                #     lambda d=new_data.copy(), s=self.data_source: (
                #         s.stream(d),
                #         print("Updated source:", s.data)
                #     )
                # )


    # def get_callback(self):
    #     return self.update_from_csv
    

    def get_plot(self) -> figure:
        return self.figure
    
    def __repr__(self):
        return f"Plot Name: {self.plot_name}:\r\nData Path: {self._data_path}\r\nX_Datetime: {self.x_datetime}\r\n(X,Y): ('{self.x_col_name}', {self.y_col_names})"

DEFAULT_CONF = '.\\config.yaml'

if len(sys.argv) == 2:
        print(colored(f"\r\n\r\nUSING CONFIG FILE: {sys.argv[1]}\r\n\r\n", 'green'))
        DEFAULT_CONF = sys.argv[1]
        # print(f"INVALID INPUT\r\nInput directory of files to convert. For example: >>> py convert_csv.py ../dummy_data_directory")
        # exit(1)
else:
    print(colored(f"\r\n\r\nNO CONFIG FILE ARGUMENT GIVEN, USING DEFAULT: {DEFAULT_CONF}\r\n\r\n", 'green'))

if not os.path.exists(DEFAULT_CONF):
    print(f"ERROR: The given path <{DEFAULT_CONF}> does not exist")
    exit(2)
config = Path(DEFAULT_CONF)

with open(config) as f:
    data = yaml.load(f, Loader=yaml.FullLoader)
    print(data)

plots_conf = data['plotter']['plots']

plots = [ Plot(p) for p in plots_conf ]


figures = []
for p in plots:
    # curdoc().add_periodic_callback(p.get_callback(), 5000)
    figures.append(p.get_plot())
    # print(p)
    # print("")

curdoc().add_root(column(*figures))
output_file(data['plotter']['title'] + '.html')
show(figures)


    # TODO: Need to hand files not found 

   
    # app.run() 




# python -m bokeh serve --address 192.168.15.61 --port 5006 --allow-websocket-origin=192.168.15.61:5006 --allow-websocket-origin=192.168.15.61:5006 --show plotter.py






  
    
    
    