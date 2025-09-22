import os
import pandas as pd
import sys

class DataProcessor():
    def __init__(self, start, end, balanced_panel, excluding_states, undergraduate_institutions):
        """
        start: start year of the panel (inclusive)
        end: end year of the panel (inclusive)
        balanced_panel: whether to construct a balanced panel 
        excluding_states: list of state abbreviations to exclude
        undergraduate_institutions: whether to restric sample into institutions that offer bachelor's degree
        """
        self.start = start
        self.end = end
        self.balanced_panel = balanced_panel
        self.excluding_states = excluding_states
        self.undergraduate_institutions = undergraduate_institutions

    def _data_loader(self):
        """
        Loads and merges Directory Information and Student Financial Aid and Net Price data by year, returning a panel data.
        """
        # Step 1: Construct folder names based on year range
        folders = []
        for year in range(self.start + 1, self.end + 2):  # shift by +1 to align with folder names
            folders.append(f"HD{year}")
            folders.append(f"SFA{str(year - 1)[-2:]}{str(year)[-2:]}")


        data_dict = {}
        for folder in folders:
            csv_filename = folder.lower() + ".csv"
            csv_path = os.path.join("Raw Data", folder, csv_filename)


            if not os.path.exists(csv_path):
                print(f"Error: {csv_path} not found!")
                sys.exit(1)

            try:
                df = pd.read_csv(csv_path, encoding='latin1')
                data_dict[folder.lower()] = df
                print(f"{folder.lower()} loaded with shape {df.shape}")
            except Exception as e:
                print(f"Failed to load {csv_path}: {e}")
                sys.exit(1)

        # Step 2: Assemble yearly panel data
        panel_dfs = []

        for year in range(self.start + 1, self.end + 2):
            hd_key = f'hd{year}'
            sfa_key = f'sfa{str(year - 1)[-2:]}{str(year)[-2:]}'
            new_year = year - 1

            if hd_key not in data_dict or sfa_key not in data_dict:
                print(f"Error: Missing data for {hd_key} or {sfa_key}")
                sys.exit(1)

            try:
                hd_df = data_dict[hd_key][['UNITID', 'STABBR', 'HLOFFER', 'UGOFFER', 'CONTROL']].copy()
                sfa_df = data_dict[sfa_key][['UNITID', 'SCUGFFN', 'FGRNT_T']].copy()
            except KeyError as e:
                print(f"Error: Required variable missing in {hd_key} or {sfa_key} — {e}")
                sys.exit(1)

            merged = pd.merge(hd_df, sfa_df, on='UNITID', how='inner')
            merged['year'] = new_year
            panel_dfs.append(merged)

        # Step 3: Concatenate all years
        panel_data = pd.concat(panel_dfs, ignore_index=True)

        # Step 4: Rename columns
        panel_data = panel_data.rename(columns={
            'UNITID': 'ID_IPEDS',
            'STABBR': 'stabbr',
            'HLOFFER': 'highest_degree',
            'UGOFFER': 'degree_bach',
            'CONTROL': 'public',
            'SCUGFFN': 'enroll_ftug',
            'FGRNT_T': 'grant_federal'
        })

        # Step 5: Clean binary columns to be 0/1
        panel_data["degree_bach"] = panel_data["degree_bach"].apply(lambda x: 1 if x == 1 else 0)
        panel_data["public"] = panel_data["public"].apply(lambda x: 1 if x == 1 else 0)


        return panel_data

    def _data_cleaner(self, panel_data):
        """
        Cleans the loaded panel data based on user-specified criteria:
        - Remove non-undergraduate institutions if undergraduate_institutions is True.
        - Remove specified states if excluding_states is not empty.
        - Keep only balanced panel data if balanced_panel is True.

        panel_data: raw panel data
        """
        panel_data_clean = panel_data.copy()

        # Step 1: Filter undergraduate institutions
        if self.undergraduate_institutions:
            panel_data_clean = panel_data_clean[panel_data_clean['degree_bach'] == 1].copy()

        # Step 2: Exclude specified states
        if isinstance(self.excluding_states, str):
            exclude_list = [self.excluding_states]
        elif isinstance(self.excluding_states, list):
            exclude_list = self.excluding_states
        else:
            raise ValueError("excluding_states must be a string or a list of strings.")

        panel_data_clean = panel_data_clean[~panel_data_clean['stabbr'].isin(exclude_list)].copy()

        # Step 3: Keep only balanced panel institutions
        if self.balanced_panel:
            panel_data_clean = panel_data_clean.dropna().copy()
            panel_data_clean['year'] = panel_data_clean['year'].astype(int)
            expected_years = set(range(self.start, self.end + 1))

            id_years = panel_data_clean.groupby('ID_IPEDS')['year'].apply(set)
            complete_ids = id_years[id_years.apply(lambda x: x == expected_years)].index
            panel_data_clean = panel_data_clean[panel_data_clean['ID_IPEDS'].isin(complete_ids)].copy()

        return panel_data_clean


    def _data_exporter(self, panel_data_clean):
        """
        Exports the cleaned panel data to a CSV file named 'clean_data.csv' in the same directory
        
        panel_data_clean: clean panel data
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(current_dir, 'clean_data.csv')

        panel_data_clean.to_csv(output_path, index=False, encoding='latin1')

        print(f"Cleaned data exported to {output_path}")



