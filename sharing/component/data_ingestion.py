import sys,os
import tarfile
import pandas as pd
import numpy as np
import scipy as sp
import shutil
from six.moves import urllib 
from sharing.exception import SharingException
from sharing.logger import logging
from sharing.entity.config_entity import DataIngestionConfig
from sharing.entity.artifact_entity import DataIngestionArtifact
from sklearn.model_selection import StratifiedShuffleSplit

class DataIngestion:
    def __init__(self,data_ingestion_config:DataIngestionConfig ):
        try:
            logging.info(f"{'='*20}Data Ingestion log started.{'='*20} ")
            self.data_ingestion_config = data_ingestion_config

        except Exception as e:
            raise SharingException(e,sys)
        
    def download_sharing_data(self,) -> str:
        try:
            #extraction remote url to download dataset
            download_url = self.data_ingestion_config.dataset_download_url
            
            #folder location to download file
            tgz_download_dir = self.data_ingestion_config.tgz_download_dir
            
            if os.path.exists(tgz_download_dir):
                os.remove(tgz_download_dir)

            os.makedirs(tgz_download_dir,exist_ok=True)
            
            # Extracting last substring from url
            sharing_file_name = os.path.basename(download_url)
            
            tgz_file_path = os.path.join(tgz_download_dir, sharing_file_name)
            logging.info(f"Downloading file from :[{download_url}] into :[{tgz_file_path}]")
            
            urllib.request.urlretrieve(download_url, tgz_file_path)
            logging.info(f"File :[{tgz_file_path}] has been downloaded successfully.")
            return tgz_file_path
        
        except Exception as e:
            raise SharingException(e,sys) from e
        
    def extract_tgz_file(self,tgz_file_path:str):
        try:
            raw_data_dir = self.data_ingestion_config.raw_data_dir
            
            if os.path.exists(raw_data_dir):
                os.remove(raw_data_dir)

            os.makedirs(raw_data_dir,exist_ok=True)
            
            logging.info(f"Extracting tgz file: [{tgz_file_path}] into dir: [{raw_data_dir}]")
            
            shutil.copy(tgz_file_path, raw_data_dir)
                
            logging.info(f"Extraction completed")
            
        except Exception as e:
            raise SharingException(e,sys) from e
        
    def split_data_as_train_test(self) -> DataIngestionArtifact:
        try:
            raw_data_dir = self.data_ingestion_config.raw_data_dir
            
            file_name = os.listdir(raw_data_dir)[0]
            
            sharing_file_path = os.path.join(raw_data_dir, file_name)
            
            logging.info(f"Reading csv file: [{sharing_file_path}]")
            sharing_data_frame = pd.read_csv(sharing_file_path)
            
            sharing_data_frame["count_cat"] = pd.cut(
                sharing_data_frame["count"],
                bins=[0.0, 1.5, 3.0, 4.5, 6.0, np.inf],
                labels=[1,2,3,4,5]
            )
            logging.info(f"Splitting data into train and test")
            strat_train_set = None
            strat_test_set = None
            
            split = StratifiedShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
            
            for train_index,test_index  in split.split(sharing_data_frame, sharing_data_frame['count_cat']):
                strat_train_set = sharing_data_frame.loc[train_index].drop(['count_cat'], axis=1)
                strat_test_set = sharing_data_frame.loc[test_index].drop(['count_cat'], axis=1)
                
            train_file_path = os.path.join(self.data_ingestion_config.ingested_train_dir,
                                           file_name)
            
            test_file_path = os.path.join(self.data_ingestion_config.ingested_test_dir,
                                        file_name)
            
            if strat_train_set is not None:
                os.makedirs(self.data_ingestion_config.ingested_train_dir, exist_ok=True)
                logging.info(f"Exporting training datset to file: [{train_file_path}]")
                strat_train_set.to_csv(train_file_path, index=False)
                
            if strat_test_set is not None:
                os.makedirs(self.data_ingestion_config.ingested_test_dir, exist_ok= True)
                logging.info(f"Exporting test dataset to file: [{test_file_path}]")
                strat_test_set.to_csv(test_file_path,index=False)
                
            data_ingestion_artifact = DataIngestionArtifact(
                train_file_path = train_file_path,
                test_file_path = test_file_path,
                is_ingested = True,
                message=f"Data ingestion completed successfully."
            )
            
            logging.info(f"Data Ingestion artifact:[{data_ingestion_artifact}]")
            return data_ingestion_artifact
            
        except Exception as e:
            raise SharingException(e,sys) from e
        
    def initiate_data_ingestion(self)-> DataIngestionArtifact:
        try:
            tgz_file_path = self.download_sharing_data()
            self.extract_tgz_file(tgz_file_path=tgz_file_path)
            return self.split_data_as_train_test()
            
        except Exception as e:
            raise SharingException(e,sys) from e
        
    def __del__(self):
        logging.info(f"{'='*20}Data Ingestion log completed.{'='*20} \n\n")
    