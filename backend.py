import random
import os
from typing import Dict, List, Union, Any

def backend_dbf(dataset: str, labeling_budget: int) -> dict:
    """
    Backend function that performs domain-based folding.
    This is a dummy implementation that will be replaced with actual logic in the future.
    
    Args:
        dataset (str): Name of the dataset to process
        labeling_budget (int): Budget for labeling
        
    Returns:
        dict: Dictionary containing domain folds in the format:
        {
            "domain_folds": {
                "Domain Fold 1": ["table1", "table2"],
                "Domain Fold 2": ["table3", "table4"],
                ...
            }
        }
    """
    # Get the actual tables from the dataset directory
    # The datasets directory is at the root level of the project
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = current_dir  # backend.py is in the root directory
    datasets_path = os.path.join(root_dir, "datasets", dataset)
    
    if not os.path.exists(datasets_path):
        print(f"Dataset path does not exist: {datasets_path}")
        return {"domain_folds": {}}
        
    # Get all subdirectories (tables) in the dataset path
    try:
        tables = [d for d in os.listdir(datasets_path) 
                if os.path.isdir(os.path.join(datasets_path, d))]
    except Exception as e:
        print(f"Error reading dataset directory: {e}")
        return {"domain_folds": {}}
    
    if not tables:
        print(f"No tables found in dataset: {dataset}")
        return {"domain_folds": {}}
    
    print(f"Found tables: {tables}")  # Debug print
    
    # Create 3 folds (or fewer if we have very few tables)
    num_folds = min(3, len(tables))
    folds = [f"Domain Fold {i+1}" for i in range(num_folds)]
    
    # Randomly assign tables to folds
    domain_folds = {fold: [] for fold in folds}
    for table in tables:
        fold = random.choice(folds)
        domain_folds[fold].append(table)
    
    # Remove empty folds
    domain_folds = {k: v for k, v in domain_folds.items() if v}
    
    return {"domain_folds": domain_folds}

def backend_qbf(selected_dataset: str, labeling_budget: int, domain_folds: Dict[str, List[str]]) -> Dict[str, Dict[str, List[Dict[str, Any]]]] :
    """
    Backend function that performs quality-based folding.
    This is a dummy implementation that will be replaced with actual logic in the future.
    
    Args:
        selected_dataset (str): Name of the dataset to process
        labeling_budget (int): Budget for labeling
        domain_folds (Dict[str, List[str]]): Dictionary mapping domain fold names to lists of table names
            Example: {
                "Domain Fold 1": ["beers", "rayyan"],
                "Domain Fold 2": ["lichess", "pokemon"]
            }
        
    Returns:
        Dict[str, Dict[str, List[Dict[str, Any]]]]: Dictionary containing cell folds in the format:
        {
            "Domain Fold 1": {
                "Domain Fold 1 / Cell Fold 1": [
                    {
                        "table": "beers",
                        "row": 42,
                        "col": "name",
                        "val": "Heineken"
                    },
                    ...
                ],
                "Domain Fold 1 / Cell Fold 2": [...],
            },
            "Domain Fold 2": {...}
        }
    """
    # Get the actual tables from the dataset directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = current_dir  # backend.py is in the root directory
    datasets_path = os.path.join(root_dir, "datasets", selected_dataset)
    
    cell_folds = {}
    
    # For each domain fold, create cell folds
    for domain_fold, tables in domain_folds.items():
        # Randomly decide to create 1 or 2 cell folds per domain fold
        num_cell_folds = random.randint(1, 2)
        cell_fold_names = [f"{domain_fold} / Cell Fold {i+1}" for i in range(num_cell_folds)]
        
        # Collect cells from each table
        cells = []
        for table in tables:
            try:
                # Read the CSV file
                table_path = os.path.join(datasets_path, table, "clean.csv")
                with open(table_path, 'r') as f:
                    # Read header line
                    header = f.readline().strip().split(',')
                    # Read a few random lines
                    lines = f.readlines()
                    if lines:
                        # Generate 3-5 random cells from this table
                        for _ in range(random.randint(3, 5)):
                            row = random.randint(0, len(lines) - 1)
                            col = random.choice(header)
                            # Get the value from the CSV line
                            values = lines[row].strip().split(',')
                            col_idx = header.index(col)
                            if col_idx < len(values):
                                val = values[col_idx]
                                cells.append({
                                    "table": table,
                                    "row": row,
                                    "col": col,
                                    "val": val
                                })
            except Exception as e:
                print(f"Error processing table {table}: {e}")
                continue
        
        # Randomly distribute cells among cell folds
        random.shuffle(cells)
        cell_fold_dict = {}
        for i, name in enumerate(cell_fold_names):
            # Distribute cells evenly among folds
            fold_cells = cells[i::num_cell_folds]
            if fold_cells:  # Only add non-empty folds
                cell_fold_dict[name] = fold_cells
        
        if cell_fold_dict:  # Only add domain folds that have cell folds
            cell_folds[domain_fold] = cell_fold_dict
    
    return cell_folds 

def backend_sample_labeling(selected_dataset: str, labeling_budget: int, cell_folds: Dict[str, Dict[str, List[Dict[str, Any]]]], domain_folds: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    """
    Backend function that samples cells for labeling.
    This is a dummy implementation that will be replaced with actual logic in the future.
    
    Args:
        selected_dataset (str): Name of the dataset to process
        labeling_budget (int): Number of cells to sample for labeling
        cell_folds (Dict[str, Dict[str, List[Dict[str, Any]]]]): Cell folds from quality-based folding
        domain_folds (Dict[str, List[str]]): Domain folds mapping
        
    Returns:
        List[Dict[str, Any]]: List of sampled cells in the format:
        [
            {
                "id": 1,
                "name": "Domain Fold 1 / Cell Fold 1 - Table1",
                "table": "Table1",
                "row": 42,
                "col": "name",
                "val": "Example",
                "domain_fold": "Domain Fold 1",
                "cell_fold": "Domain Fold 1 / Cell Fold 1"
            },
            ...
        ]
    """
    # Get the actual tables from the dataset directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = current_dir  # backend.py is in the root directory
    datasets_path = os.path.join(root_dir, "datasets", selected_dataset)
    
    # Collect all available cells from cell folds
    all_cells = []
    for domain_fold, cell_fold_dict in cell_folds.items():
        for cell_fold_name, cells in cell_fold_dict.items():
            for cell in cells:
                cell_info = {
                    "table": cell["table"],
                    "row": cell["row"],
                    "col": cell["col"],
                    "val": cell["val"],
                    "domain_fold": domain_fold,
                    "cell_fold": cell_fold_name
                }
                all_cells.append(cell_info)
    
    # If we don't have enough cells in cell_folds, generate additional random cells
    if len(all_cells) < labeling_budget:
        # Get all tables from domain folds
        all_tables = []
        for tables in domain_folds.values():
            all_tables.extend(tables)
        
        # Generate additional random cells
        while len(all_cells) < labeling_budget:
            table = random.choice(all_tables)
            try:
                # Read the CSV file
                table_path = os.path.join(datasets_path, table, "clean.csv")
                with open(table_path, 'r') as f:
                    header = f.readline().strip().split(',')
                    lines = f.readlines()
                    if lines:
                        row = random.randint(0, len(lines) - 1)
                        col = random.choice(header)
                        values = lines[row].strip().split(',')
                        col_idx = header.index(col)
                        if col_idx < len(values):
                            val = values[col_idx]
                            # Find the domain fold for this table
                            domain_fold = next(
                                (fold for fold, tables in domain_folds.items() if table in tables),
                                "Unknown Domain"
                            )
                            cell_info = {
                                "table": table,
                                "row": row,
                                "col": col,
                                "val": val,
                                "domain_fold": domain_fold,
                                "cell_fold": f"{domain_fold} / Random Sample"
                            }
                            if cell_info not in all_cells:  # Avoid duplicates
                                all_cells.append(cell_info)
            except Exception as e:
                print(f"Error processing table {table}: {e}")
                continue
    
    # Randomly sample labeling_budget cells
    sampled_cells = random.sample(all_cells, min(labeling_budget, len(all_cells)))
    
    # Format the output
    return [
        {
            "id": i,
            "name": f"{cell['domain_fold']} – {cell['table']}",
            "table": cell['table'],
            "row": cell['row'],
            "col": cell['col'],
            "val": cell['val'],
            "domain_fold": cell['domain_fold'],
            "cell_fold": cell['cell_fold']
        }
        for i, cell in enumerate(sampled_cells)
    ] 