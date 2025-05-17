import random
import os

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