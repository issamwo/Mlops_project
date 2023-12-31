import os
import re
import pandas as pd
import numpy as np
import string
import json
from Classifier import logger
from Classifier.entity.config_entity import DataCleaningConfig


class DataCleaning:
    def __init__(self, config: DataCleaningConfig): 
        self.config = config
    
    def detect_last_file(self) -> str:
        """
        get last unzip files from the ingestion pipeline
        """
        logger.info("Looking for all JSON files to Select latest one download/created")
        directory = self.config.unpreprocessed_data_path
        json_files = [f for f in os.listdir(directory) if f.endswith('.json')]
        max_element = None
        max_output = float('-inf')

        for element in json_files:
            output = os.path.getctime(os.path.join(os.getcwd(), directory,element))
            if output > max_output:
                max_output = output
                max_element = element
        logger.info(f"latest file detected: {max_element}")
        return os.path.join(os.getcwd(), directory,max_element)

    def read_data(self, file_path: str) -> pd.DataFrame:
        """
        read and subset the data
        """
        
        logger.info("Read unprocessed file")
        column_text = self.config.column_text
        column_topic = self.config.column_topic
        # Load the JSON file as a string
        with open(file_path) as f:
            data = json.load(f)
        # Normalize the JSON data and create a DataFrame
        df = pd.json_normalize(data)
        # Subset of data
        df = df.loc[:, [column_text, column_topic]]
        logger.info("File read is completed")
        return df
        
    
    def clean_data(self, df: pd.DataFrame):
        '''This function 
            - Clean column name
            - Drop NA's
            - makes the given text lowercase
            - removes text in square brackets
            - removes punctuation and 
            - removes words containing numbers.
        :param text: text to be cleaned
        :return: cleaned text
        '''
        column_text = self.config.column_text
        cleaned_data_path = self.config.cleaned_data_path

        os.makedirs("artifacts/data_cleaning", exist_ok=True)


        # Assign nan in place of blanks in the complaints column
        df[column_text].replace("", np.nan, inplace=True)
        #Remove all rows where complaints column is nan
        df.dropna(subset=[column_text], inplace=True)
        # Make the text lowercase
        df[column_text] = pd.DataFrame(df[column_text].apply(lambda x: x.lower()))
        # Remove text in square brackets
        df[column_text] = pd.DataFrame(df[column_text].apply(lambda x: re.sub(r'\[.*?\]', '', x)))    
        # Remove punctuation
        df[column_text] = pd.DataFrame(
                            df[column_text].apply(lambda x: re.sub(r'[%s]' % re.escape(string.punctuation), '', x))
                            )    
        # Remove words containing numbers
        df[column_text] = pd.DataFrame(df[column_text].apply(lambda x: re.sub(r'\w*\d\w*', '', x)))
        
        try:
            logger.info(f"Started the downloading of cleaned data into file {cleaned_data_path}")
            json_data = df.to_json(orient='records')
            with open(os.path.join(cleaned_data_path,'cleaned_data.json'), 'w') as f:
                f.write(json_data)
            logger.info(f"downloaded  cleaned data into file {cleaned_data_path} Completed")
        except Exception as e:
            raise e