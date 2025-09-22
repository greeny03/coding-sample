import os
import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from shapely.affinity import scale, translate
from mpl_toolkits.axes_grid1 import make_axes_locatable

class MapMaker():
    def __init__(self, data, col, export_name):
        """
        data: a DataFrame with 'stabbr', 'year' and data needed to visualize on the map
        col: the specific column name of data to visualize
        export_name: exporting name of the image
        """
        self.data = data
        self.col = col
        self.export_name = export_name
        
    def _map_figure(self):
        """
        Visualizes the data on the map
        """
        # Step 1: Import U.S. shape file (Downloaded from https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_state_20m.zip)
        shapefile_path = './cb_2018_us_state_20m/cb_2018_us_state_20m.shp'
        states = gpd.read_file(shapefile_path)
        state_list = [
            'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
            'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
            'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
            'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
            'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
        ]
        states = states[states['STUSPS'].isin(state_list)]
        states = states.merge(self.data, left_on='STUSPS', right_on='stabbr')

        mainland = states[~states['STUSPS'].isin(['AK', 'HI'])]
        alaska = states[states['STUSPS'] == 'AK']
        hawaii = states[states['STUSPS'] == 'HI']

        # Step 2: Resize the Alaska map to fit within the overall figure
        alaska = alaska.copy()
        alaska['geometry'] = alaska['geometry'].apply(lambda geom: scale(geom, xfact=0.2, yfact=0.2, origin='center'))
        alaska['geometry'] = alaska['geometry'].apply(lambda geom: translate(geom, xoff=-100, yoff=-10))

        # Step 3: Visualize the data on the map using a color scale
        vmin, vmax = states[self.col].min(), states[self.col].max()
        norm = plt.Normalize(vmin=vmin, vmax=vmax)
        fig = plt.figure(figsize=(24, 6))
        gs = GridSpec(1, 2, width_ratios=[1, 50], wspace=-0.8)
        ax_hi = fig.add_subplot(gs[0, 0])
        hawaii.plot(column=self.col, cmap='RdYlBu_r', linewidth=0.8, edgecolor='0.8', 
                    ax=ax_hi, norm=norm)
        ax_hi.axis('off')
        ax_main = fig.add_subplot(gs[0, 1])
        mainland.plot(column=self.col, cmap='RdYlBu_r', linewidth=0.8, edgecolor='0.8', 
                      ax=ax_main, norm=norm)
        alaska.plot(column=self.col, cmap='RdYlBu_r', linewidth=0.8, edgecolor='0.8', 
                    ax=ax_main, norm=norm)
        
        # Step 4: Add title and state abbreviations to the map
        ax_main.set_title(f'{self.export_name}', fontsize=12)
        ax_main.axis('off')

        offsets = {
            'RI': (1.5, -0.5),
            'CT': (1.2, -1),
            'DE': (1.2, -1.2),
            'MD': (1.8, 0),
            'NJ': (1.5, 0.2),
            'MA': (1.5, 1),
            'VT': (1.5, 1.5),
            'NH': (1.8, 0.9),
        }
        for idx, row in mainland.iterrows():
            abbr = row['STUSPS']
            x, y = row['geometry'].centroid.coords[0]
            if abbr in offsets:
                dx, dy = offsets[abbr]
                ax_main.annotate(
                    abbr,
                    xy=(x, y),
                    xytext=(x + dx, y + dy),
                    fontsize=8,
                    color='black',
                    ha='left', va='center',
                    arrowprops=dict(arrowstyle='->', color='black', lw=0.5)
                )
            else:
                ax_main.text(x, y, abbr, fontsize=8, color='black', ha='center', va='center')

        for idx, row in alaska.iterrows():
            x, y = row['geometry'].centroid.coords[0]
            ax_main.text(x, y, row['STUSPS'], fontsize=8, color='black', ha='center', va='center')

        for idx, row in hawaii.iterrows():
            x, y = row['geometry'].centroid.coords[0]
            ax_hi.text(x, y, row['STUSPS'], fontsize=8, color='black', ha='center', va='center')

        # Step 5: Add a colorbar on the left to indicate the data values, and save the entire figure
        divider = make_axes_locatable(ax_main)
        cax = divider.append_axes("left", size="0.5%", pad=0.1)
        sm = plt.cm.ScalarMappable(cmap='RdYlBu_r', norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, cax=cax)
        cbar.set_label('Grant per Student', rotation=270, labelpad=12)
        plt.subplots_adjust(left=0.01, right=0.99, top=0.97, bottom=0)
        fig_path = os.path.join(os.getcwd(), 'Figure', f'{self.export_name}.png')
        plt.savefig(fig_path, dpi=300, bbox_inches='tight')
        #plt.show()