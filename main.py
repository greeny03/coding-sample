###### main #####
"""
Region 1: Assembling the Data
Loads, cleans, and exports panel data from 2010–2015 using DataProcessor, excluding certain territories and focusing on undergraduate institutions.

Region 2: Trend of Enrollment
Reads cleaned data, filters for public two-year colleges, aggregates enrollment by year, plots a line chart of total enrollment, and saves the figure.

Region 3: Facts of Financial Aid
Analyzes per-student federal grants in 2015 using DataAnalyzer.
a) Compares New York vs Vermont with a bar chart.
b) Produces descriptive statistics and regional mean/variance tables, outputs LaTeX and a figure.
c) Simulates grant allocation with a formula, generates statistics and tables, outputs LaTeX and a figure.

Region 4: Visualize Results in Maps
Creates maps at the state level for actual and simulated per-student federal grants
"""

# region: 1 Assembling the Data
from DataProcessor import DataProcessor
processor = DataProcessor(
    start=2010,
    end=2015,
    balanced_panel=True,
    excluding_states=['DC', 'FM', 'MH', 'MP', 'PR', 'PW', 'VI', 'GU', 'AS'],
    undergraduate_institutions=True
)
df = processor._data_loader()
df = processor._data_cleaner(panel_data = df)
processor._data_exporter(panel_data_clean = df)
# endregion

# region: 2 Trend of enrollment
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

df = pd.read_csv('clean_data.csv', encoding='latin1')
filtered_df = df[(df['highest_degree'].isin([1, 2, 3, 4])) & (df['public'] == 1)].copy()
enroll_by_year = filtered_df.groupby('year')['enroll_ftug'].sum().reset_index()
enroll_by_year['academic_year'] = enroll_by_year['year'].apply(lambda y: f"{y}-{str(y+1)[-2:]}")

plt.figure(figsize=(8, 5))
plt.plot(enroll_by_year['academic_year'], enroll_by_year['enroll_ftug'], marker='o', linestyle='-')
plt.title('Total number of students enrolled at all public, two-year colleges by Academic Year')
plt.xlabel('Academic Year')
plt.ylabel('Total number of students enrolled at all public, two-year colleges')
plt.gca().yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))
plt.grid(True)
plt.tight_layout()
plt.xticks(rotation=45)
# outout path
fig_path = os.path.join(os.getcwd(), 'Figure', 'public_two_year_colleges_enroll_by_year.png')
plt.savefig(fig_path, dpi=300, bbox_inches='tight')
#plt.show()
# endregion

# region: 3 Facts of financial aid
import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.table import Table
from DataAnalyzer import DataAnalyzer

df = pd.read_csv('clean_data.csv', encoding='latin1')
analyzer = DataAnalyzer(
    clean_data = df, 
    year = 2015, 
    formula = [1750, 0.15]
)
state_data = analyzer._aggregate_per_student_grant()

# region: a Compare and visualize (NY v.s. VT)
selected_states = ['NY', 'VT']
filtered_data = state_data[state_data['stabbr'].isin(selected_states)]

# Code block for generating a bar chart
plt.figure(figsize=(5, 4))
bars = plt.bar(
    filtered_data['stabbr'],
    filtered_data['per_student_federal_grant'],
    color='gray'
)
plt.ylim(0, filtered_data['per_student_federal_grant'].max() * 1.5)
for bar in bars:
    height = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        height + 50,
        f'{height:,.2f}',
        ha='center',
        va='bottom',
        color='black',
        fontsize=11
    )
plt.title('Per Student Federal Grant: NY vs VT (2015-16)')
plt.xlabel('State')
plt.ylabel('Per Student Federal Grant')
plt.tight_layout()
fig_path = os.path.join(os.getcwd(), 'Figure', 'per_student_federal_grant_ny_vs_vt.png')
plt.savefig(fig_path, dpi=300, bbox_inches='tight')
#plt.show()
#endregion

# region: b Summary Statistics across States
desc_stats, region_stats = analyzer._summary_statistics(state_data, 'per_student_federal_grant')

# Code block for generating a table figure
desc_long = desc_stats.T.reset_index()
desc_long.columns = ['Variable', 'Value']
region_stats_renamed = region_stats.rename(columns={
    'census_region': 'Region',
    'mean': 'Mean',
    'var': 'Variance'
})
region_list = []
for _, row in region_stats_renamed.iterrows():
    region_list.append({'Variable': f"{row['Region']} Mean", 'Value': row['Mean']})
    region_list.append({'Variable': f"{row['Region']} Variance", 'Value': row['Variance']})

region_long = pd.DataFrame(region_list)

full_long = pd.concat([desc_long, region_long], ignore_index=True)

latex_code = full_long.to_latex(index=False,
                               caption="Descriptive Statistics and Regional Means and Variances",
                               label="tab:desc_region_stats",
                               float_format="%.3f")
print(latex_code)
fig, ax = plt.subplots(figsize=(6, max(4, 0.3 * len(full_long))))
ax.axis('off')
plt.title("Per-student Federal Grant 2015-16", fontsize=14, fontweight='bold')
tbl = Table(ax, bbox=[0, 0, 1, 1])
n_rows, n_cols = full_long.shape
cell_w = 1.0 / n_cols
cell_h = 1.0 / (n_rows + 1)
for j, colname in enumerate(full_long.columns):
    tbl.add_cell(0, j, cell_w, cell_h, text=colname, loc='center', facecolor='#CCCCCC')
for i in range(n_rows):
    for j in range(n_cols):
        val = full_long.iat[i, j]
        if isinstance(val, float):
            val = f"{val:.3f}"
        tbl.add_cell(i + 1, j, cell_w, cell_h, text=str(val), loc='center', facecolor='white')
ax.add_table(tbl)
plt.tight_layout()
fig_path = os.path.join(os.getcwd(), 'Figure', 'descriptive_statistics_table.png')
plt.savefig(fig_path, dpi=300, bbox_inches='tight')
#plt.show()
#endregion

# region: c Simulate with given foumula
simulated_data = analyzer._simulater()
desc_stats, region_stats = analyzer._summary_statistics(simulated_data, 'grant_per_student_simulated')

# Code block for generating a table figure
desc_long = desc_stats.T.reset_index()
desc_long.columns = ['Variable', 'Value']

region_stats_renamed = region_stats.rename(columns={
    'census_region': 'Region',
    'mean': 'Mean',
    'var': 'Variance'
})

region_list = []
for _, row in region_stats_renamed.iterrows():
    region_list.append({'Variable': f"{row['Region']} Mean", 'Value': row['Mean']})
    region_list.append({'Variable': f"{row['Region']} Variance", 'Value': row['Variance']})

region_long = pd.DataFrame(region_list)

full_long = pd.concat([desc_long, region_long], ignore_index=True)

latex_code = full_long.to_latex(index=False,
                               caption="Descriptive Statistics and Regional Means and Variances (Simulated)",
                               label="tab:desc_region_stats",
                               float_format="%.3f")
print(latex_code)

fig, ax = plt.subplots(figsize=(6, max(4, 0.3 * len(full_long))))
ax.axis('off')
plt.title("Grant per-student Simulated 2015-16", fontsize=14, fontweight='bold')

tbl = Table(ax, bbox=[0, 0, 1, 1])

n_rows, n_cols = full_long.shape
cell_w = 1.0 / n_cols
cell_h = 1.0 / (n_rows + 1)

for j, colname in enumerate(full_long.columns):
    tbl.add_cell(0, j, cell_w, cell_h, text=colname, loc='center', facecolor='#CCCCCC')

for i in range(n_rows):
    for j in range(n_cols):
        val = full_long.iat[i, j]
        if isinstance(val, float):
            val = f"{val:.3f}"
        tbl.add_cell(i + 1, j, cell_w, cell_h, text=str(val), loc='center', facecolor='white')

ax.add_table(tbl)
plt.tight_layout()
fig_path = os.path.join(os.getcwd(), 'Figure', 'descriptive_statistics_table (Simulated).png')
plt.savefig(fig_path, dpi=300, bbox_inches='tight')
#plt.show()
#endregion
#endregion

# region: 4 Visualize results in maps
from MapMaker import MapMaker

real_data_map = MapMaker(
     data = state_data,
     col = 'per_student_federal_grant',
     export_name = 'Federal Grant per Student by State (2015-16)'
)
real_data_map._map_figure()

simulated_data_map = MapMaker(
    data = simulated_data,
    col = 'grant_per_student_simulated',
    export_name = 'Grant per Student Simulated by State (2015-16)'
)
simulated_data_map._map_figure()
# endregion