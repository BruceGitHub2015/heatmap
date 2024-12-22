import pandas as pd

def data_processing(data):
    split_indices = [i for i, col in enumerate(data.columns) if pd.isna(data.iloc[0, i])]
    table1_columns, table2_columns = [], []
    
    if not split_indices:
        combined_table = data.dropna()
        table1_columns = data.columns.tolist()
    else:
        # Handle split into two tables
        split_idx = split_indices[0]
        table1 = data.iloc[:, :split_idx].dropna()
        table2 = data.iloc[:, split_idx + 1:].dropna()        
    
        # Automatically remove columns with all zeros after splitting
        table1 = table1.loc[:, (table1 != 0).any(axis=0)]
        table2 = table2.loc[:, (table2 != 0).any(axis=0)]

        table1_columns = table1.columns.tolist()
        table2_columns = table2.columns.tolist()
        
        if table2.empty:
            combined_table = table1
        else:
            # Match rows in the first table to the second table by closest time using column indices
            smaller_time = table2.iloc[:, 1].dropna().sort_values()
            larger_time = table1.iloc[:, 1].dropna().sort_values()  
            
            matched_indices = []
            j = 0
            for t in smaller_time:
                while j < len(larger_time) - 1 and abs(larger_time.iloc[j + 1] - t) < abs(larger_time.iloc[j] - t):
                    j += 1
                matched_indices.append(larger_time.index[j])           
    
            matched_rows = table1.loc[matched_indices].reset_index(drop=True)                 
    
            # Combine the tables
            combined_table = pd.concat([table2.reset_index(drop=True), matched_rows], axis=1).dropna()
    return combined_table, table1_columns, table2_columns
