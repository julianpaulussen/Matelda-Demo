import hashlib
import json
import os
from datetime import datetime

import numpy as np
import pandas as pd
import torch
from sklearn.cluster import HDBSCAN


def get_tables_hash(tables):
    """
    Generate a hash of the table list to detect changes in the dataset.
    """
    tables_str = ",".join(sorted(tables))
    return hashlib.md5(tables_str.encode()).hexdigest()


def load_from_cache(cache_dir, tables):
    """
    Load domain folds from cache if available and valid.

    Args:
        cache_dir (str): Path to cache directory
        tables (list): Current list of tables

    Returns:
        dict or None: Cached domain folds if valid, None otherwise
    """
    cache_file = os.path.join(cache_dir, "domain_folds_cache.json")

    if not os.path.exists(cache_file):
        return None

    try:
        with open(cache_file, "r") as f:
            cache_data = json.load(f)

        # Check if cache is valid (same tables)
        current_hash = get_tables_hash(tables)
        cached_hash = cache_data.get("tables_hash")

        if current_hash == cached_hash:
            print(f"Cache hit! Last computed: {cache_data.get('timestamp', 'unknown')}")
            return cache_data.get("domain_folds")
        else:
            print("Cache invalid: dataset has changed")
            return None

    except Exception as e:
        print(f"Error reading cache: {e}")
        return None


def save_to_cache(cache_dir, tables, domain_folds):
    """
    Save domain folds to cache.

    Args:
        cache_dir (str): Path to cache directory
        tables (list): List of tables
        domain_folds (dict): Domain folds to cache
    """
    cache_file = os.path.join(cache_dir, "domain_folds_cache.json")

    cache_data = {
        "timestamp": datetime.now().isoformat(),
        "tables_hash": get_tables_hash(tables),
        "tables": tables,
        "domain_folds": domain_folds,
    }

    try:
        with open(cache_file, "w") as f:
            json.dump(cache_data, f, indent=2)
        print(f"Domain folds cached successfully at {cache_file}")
    except Exception as e:
        print(f"Error saving cache: {e}")


def matelda_domain_folding(datasets_path, tables):
    """
    Domain-based Cell Folding

    1. Serialize each table by concatenating all cell values
    2. Generate BERT embeddings
    3. Apply HDBSCAN clustering
    """
    # Step 1: Initialize BERT model with fallback options
    model_name = "bert-base-uncased"

    try:
        # Try PyTorch first
        from transformers import AutoModel, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name)

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)
        model.eval()
        framework = "pytorch"

    except Exception as pytorch_error:
        print(f"ERROR:root:Error loading model {model_name}: {pytorch_error}")
        try:
            # Fallback to TensorFlow
            from transformers import AutoTokenizer, TFAutoModel

            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = TFAutoModel.from_pretrained(model_name, from_tf=True)
            framework = "tensorflow"
            print("Using TensorFlow backend as fallback")

        except Exception as tf_error:
            print(f"TensorFlow fallback also failed: {tf_error}")
            return None

    # Step 2: Generate contextual embeddings (CE)
    CE = []  # Set of contextual embeddings
    valid_tables = []

    for table in tables:
        table_path = os.path.join(datasets_path, table)

        csv_files = [f for f in os.listdir(table_path) if f.endswith(".csv")]
        if not csv_files:
            continue

        try:
            # Read CSV file
            csv_path = os.path.join(table_path, csv_files[0])
            df = pd.read_csv(csv_path)

            st = serialize_table(df)

            if st:
                if framework == "pytorch":
                    ce = obtain_BERT_Embedding_pytorch(st, tokenizer, model, device)
                else:
                    ce = obtain_BERT_Embedding_tensorflow(st, tokenizer, model)

                CE.append(ce)
                valid_tables.append(table)

        except Exception as e:
            print(f"Error processing table {table}: {e}")
            continue

    if len(valid_tables) < 2:
        return None

    # Step 3: HDBSCAN(CE)
    embeddings_array = np.array(CE)

    clustering = HDBSCAN(min_cluster_size=2, min_samples=1)
    cluster_labels = clustering.fit_predict(embeddings_array)

    # Organize into domain folds - each cluster is a Domain Fold df
    DFolds = {}
    outlier_count = 0

    for table, label in zip(valid_tables, cluster_labels):
        if label == -1:  # Outlier - individual group
            outlier_count += 1
            fold_name = f"Domain Fold {outlier_count}"
            DFolds[fold_name] = [table]
        else:
            fold_name = f"Domain Fold {label + 1}"
            if fold_name not in DFolds:
                DFolds[fold_name] = []
            DFolds[fold_name].append(table)

    return DFolds


def serialize_table(df):
    """

    Concatenate all cell values in a row into a single string,
    then concatenate 10 rows into a larger string to treat table as single sentence.
    """
    try:
        df = df.head(10)  # Limit to first 10 rows for serialization
        text = " ".join(df.values.astype(str).flatten())
        processed_text = preprocess_text(text)

        return processed_text

    except Exception as e:
        print(f"Error serializing table: {e}")
        return None


def preprocess_text(text):
    """
    Preprocessing steps:
    1. Convert text to lowercase
    2. Remove English stop words
    """
    from nltk.corpus import stopwords

    # Ensure nltk stopwords are available
    try:
        nltk_stopwords = set(stopwords.words("english"))
    except:
        # If NLTK data not available, use basic stop words
        nltk_stopwords = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "can",
            "this",
            "that",
            "these",
            "those",
            "i",
            "you",
            "he",
            "she",
            "it",
            "we",
            "they",
            "me",
            "him",
            "her",
            "us",
            "them",
        }

    text = text.lower()

    words = text.split()
    words = [word for word in words if word not in nltk_stopwords]

    return " ".join(words)


def obtain_BERT_Embedding_pytorch(st, tokenizer, model, device):
    """
    Generate BERT feature vector for the serialized table to capture
    its semantic characteristics.
    """
    with torch.no_grad():
        # Tokenize the serialized table string
        inputs = tokenizer(
            st, return_tensors="pt", max_length=512, truncation=True, padding=True
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}

        # Get BERT output
        outputs = model(**inputs)

        embedding = outputs.last_hidden_state[:, 0, :].squeeze()

        return embedding.cpu().numpy()


def obtain_BERT_Embedding_tensorflow(st, tokenizer, model):
    """
    Generate BERT feature vector for the serialized table to capture
    its semantic characteristics.
    """

    # Tokenize the serialized table string
    inputs = tokenizer(
        st, return_tensors="tf", max_length=512, truncation=True, padding=True
    )

    # Get BERT output
    outputs = model(**inputs)

    # Use [CLS] token embedding as table representation
    embedding = outputs.last_hidden_state[:, 0, :].numpy().squeeze()

    return embedding
