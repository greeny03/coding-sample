class DataAnalyzer():
    def __init__(self, clean_data, year, formula):
        """
        clean_data: clean panel data
        year: the specific year to analyze
        formula: a list of two numeric values representing the coefficients for the simulation formula—
        the first for the linear term and the second for the quadratic term
        """
        self.clean_data = clean_data
        self.year = year
        self.formula = formula


    def _aggregate_per_student_grant(self):
        """
        Aggregates federal grant and enrollment by state, computing per-student grants for the specified year.
        """
        # Step 1: Filter data for the specified year
        data_year = self.clean_data[self.clean_data['year'] == self.year].copy()

        # Step 2: Group by 'stabbr' and sum 'grant_federal' and 'enroll_ftug'
        grouped = data_year.groupby('stabbr').agg({
            'grant_federal': 'sum',
            'enroll_ftug': 'sum'
        }).reset_index()

        # Step 3: Calculate per-student federal grant, avoid division by zero
        grouped['per_student_federal_grant'] = grouped.apply(
            lambda row: row['grant_federal'] / row['enroll_ftug'] if row['enroll_ftug'] > 0 else 0,
            axis=1
        )
        grouped['year'] = self.year

        return grouped

    def _summary_statistics(self, data, col):
        """
        Computes descriptive and region-level statistics for per-student federal grants.

        data: a DataFrame with 'stabbr', 'per_student_federal_grant', and 'year'
        col: the specific column name of the data to summary
        """

        # National descriptive stats
        desc_stats = data[col].describe(percentiles=[0.25, 0.5, 0.75]).to_frame().T
        desc_stats['variance'] = data[col].var()

        # Census region mapping
        census_regions = {
            'Northeast': ['ME', 'NH', 'VT', 'MA', 'RI', 'CT', 'NY', 'NJ', 'PA'],
            'Midwest': ['OH', 'IN', 'IL', 'MI', 'WI', 'MN', 'IA', 'MO', 'ND', 'SD', 'NE', 'KS'],
            'South': ['DE', 'MD', 'VA', 'WV', 'NC', 'SC', 'GA', 'FL', 'KY', 'TN', 'MS', 'AL', 'OK', 'TX', 'AR', 'LA'],
            'West': ['WA', 'OR', 'CA', 'NV', 'ID', 'MT', 'WY', 'CO', 'NM', 'AZ', 'UT', 'AK', 'HI']
        }
        state_to_region = {}
        for region, states in census_regions.items():
            for state in states:
                state_to_region[state] = region
        data['census_region'] = data['stabbr'].map(state_to_region)

        # Region-level stats
        region_stats = data.groupby('census_region')[col].agg(['mean', 'var']).reset_index()

        return desc_stats, region_stats

        
    def _simulater(self):
        """
        Simulates per-student federal grants using a quadratic formula at the school level
        """
        # Step 1: Extract coefficients from formula
        a, b = self.formula

        # Step 2: Filter by specified year
        df = self.clean_data[self.clean_data['year'] == self.year].copy()

        # Step 3: Compute simulated federal grants for each school
        df['grant_federal_simulated'] = (
            a * df['enroll_ftug'] +
            b * (df['enroll_ftug'] ** 2)
        )

        # Step 4: Group by state and sum enrollments and simulated grants
        state_grouped = df.groupby('stabbr').agg({
            'enroll_ftug': 'sum',
            'grant_federal_simulated': 'sum'
        }).reset_index()

        # Step 5: Compute per-student simulated grants
        state_grouped['grant_per_student_simulated'] = state_grouped.apply(
            lambda row: row['grant_federal_simulated'] / row['enroll_ftug'] if row['enroll_ftug'] > 0 else 0,
            axis=1
        )
        state_grouped['year'] = self.year

        return state_grouped[['year', 'stabbr', 'grant_per_student_simulated']]
