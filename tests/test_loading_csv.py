import csv
import pandas as pd

file_name_csv = "./sample_csv_lenses.csv"
file_name_json = "/Users/henrybest/Downloads/lenses.json"

current_targets = pd.read_csv(file_name_csv)
current_targets = pd.read_json(file_name_json)



print(current_targets)
