import pandas as pd
import numpy as np
import re

def clean_financial_data(file):
    try:
        df = pd.read_excel(file, engine='openpyxl')
    except Exception:
        df = pd.read_csv(file)

    # Drop completely empty rows and columns
    df.dropna(axis=0, how='all', inplace=True)
    df.dropna(axis=1, how='all', inplace=True)

    # Reset header if necessary
    if not df.columns.str.contains(r'[A-Za-z]').any():
        df.columns = df.iloc[0]
        df = df[1:]

    df.columns = [str(col).strip() for col in df.columns]

    # Standardize numeric columns
    for col in df.columns:
        df[col] = df[col].astype(str).str.replace(',', '', regex=False)
        df[col] = df[col].str.replace(r'\((.*?)\)', r'-\1', regex=True)  # (1000) → -1000
        df[col] = df[col].str.replace(r'[%₹$]', '', regex=True)
        
        # Try to convert to numeric, leave text columns untouched
        try:
            df[col] = pd.to_numeric(df[col], errors='ignore')
        except Exception:
            pass

    # Convert dates
    for col in df.columns:
        try:
            df[col] = pd.to_datetime(df[col], errors='ignore', dayfirst=True)
        except Exception:
            pass

    # Fill missing numeric values with interpolation or zeros
    num_cols = df.select_dtypes(include=['number']).columns
    df[num_cols] = df[num_cols].fillna(method='ffill').fillna(method='bfill').fillna(0)

    # Strip all string columns
    obj_cols = df.select_dtypes(include=['object']).columns
    df[obj_cols] = df[obj_cols].apply(lambda x: x.str.strip())

    return df
