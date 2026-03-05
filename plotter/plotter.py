
import sys
import os.path
from pathlib import Path
import random
import yaml
import numpy as np
import pandas as pd
import statistics as stats
from bokeh.plotting import figure, show, curdoc
from bokeh.models import HoverTool, DatetimeTickFormatter
from bokeh.models.formatters import TickFormatter
from bokeh.io import output_file, show
import datetime

BOKEH_COLORS = [ 
    'aliceblue',
    'aqua',
    'aquamarine',
    'azure',
    'beige',
    'bisque',
    'black',
    'blanchedalmond',
    'blue',
    'blueviolet',
    'brown',
    'burlywood',
    'cadetblue',
    'chartreuse',
    'chocolate',
    'coral',
    'cornflowerblue',
    'cornsilk',
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
    'floralwhite',
    'forestgreen',
    'fuchsia',
    'gainsboro',
    'ghostwhite',
    'gold',
    'goldenrod',
    'gray',
    'green',
    'greenyellow',
    'grey',
    'honeydew',
    'hotpink',
    'indianred',
    'indigo',
    'ivory',
    'khaki',
    'lavender',
    'lavenderblush',
    'lawngreen',
    'lemonchiffon',
    'lightblue',
    'lightcoral',
    'lightcyan',
    'lightgoldenrodyellow',
    'lightgray',
    'lightgreen',
    'lightgrey',
    'lightpink',
    'lightsalmon',
    'lightseagreen',
    'lightskyblue',
    'lightslategray',
    'lightslategrey',
    'lightsteelblue',
    'lightyellow',
    'lime',
    'limegreen',
    'linen',
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
    'mintcream',
    'mistyrose',
    'moccasin',
    'navajowhite',
    'navy',
    'oldlace',
    'olive',
    'olivedrab',
    'orange',
    'orangered',
    'orchid',
    'palegoldenrod',
    'palegreen',
    'paleturquoise',
    'palevioletred',
    'papayawhip',
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
    'seashell',
    'sienna',
    'silver',
    'skyblue',
    'slateblue',
    'slategray',
    'slategrey',
    'snow',
    'springgreen',
    'steelblue',
    'tan',
    'teal',
    'thistle',
    'tomato',
    'turquoise',
    'violet',
    'wheat',
    'white',
    'whitesmoke',
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
        self.figure = None


        if (self._load_csv() != SUCCESSFUL) or (self._validate_columns() != SUCCESSFUL):
            return
        
        self.generate_plot()
        
        
    
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


    def generate_plot(self): 
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
            
            # self.figure = figure(x_axis_type='datetime',width=DEFAULT_PLOT_WIDTH, height=DEFAULT_PLOT_HEIGHT, title=self.plot_name, tooltips=DEFAULT_TOOLTIPS)
            self._df[self.x_col_name] = pd.to_datetime(self._df[self.x_col_name])
            self.figure = figure(x_axis_type='datetime',width=DEFAULT_PLOT_WIDTH, height=DEFAULT_PLOT_HEIGHT, title=self.plot_name)
            self.figure.add_tools(custom_hover)
            
            
        else:
            self.figure = figure(width=DEFAULT_PLOT_WIDTH, height=DEFAULT_PLOT_HEIGHT, title=self.plot_name, tooltips=DEFAULT_TOOLTIPS)
        
        # For multiple y columns
        for y_col in self.y_col_names:
            rand_color = BOKEH_COLORS[random.randint(0, COLOURS_LENGTH - 1)]
            self.figure.scatter(x=self._df[self.x_col_name], y=self._df[y_col], size=4, legend_label = y_col, color=rand_color)

        self.figure.xgrid.grid_line_color = 'navy'

        


    def get_plot(self) -> figure:
        return self.figure
    
    def __repr__(self):
        return f"Plot Name: {self.plot_name}:\r\nData Path: {self._data_path}\r\nX_Datetime: {self.x_datetime}\r\n(X,Y): ('{self.x_col_name}', {self.y_col_names})"

DEFAULT_CONF = '.\\config.yaml'

if __name__ == '__main__':
    if not os.path.exists(DEFAULT_CONF):
        print(f"ERROR: The given path <{DEFAULT_CONF}> does not exist")
        exit(2)
    config = Path(DEFAULT_CONF)

    with open('config.yaml') as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        print(data)

    plots_conf = data['plotter']

    plots = [ Plot(p) for p in plots_conf]

    for p in plots:
        print(p)
        print("")
    output_file('plotter_output.html')
    figures = [p.get_plot() for p in plots]
    show(figures)
    
    # curdoc().title("My Plots Super Cool")
    # curdoc().set_title()
    # for f in figures:
    #     curdoc().add_root(f)
    
    
    