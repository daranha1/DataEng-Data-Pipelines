from datetime import datetime, timedelta
import os
from airflow import DAG
from airflow.contrib.hooks.aws_hook import AwsHook
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.postgres_operator import PostgresOperator
from operators import (StageToRedshiftOperator, LoadFactOperator,
                                LoadDimensionOperator, DataQualityOperator)
from helpers import SqlQueries


"""
   This dag executes the steps involved in an Airflow Pipeline
   More specifically, the following sequence is involved
   A. Creating seven tables using the Postgres Operator:
      Tables: staging_events, staging_songs, songplays, artists, songs, users, and time 
   B. Staging Tables using the StageToRedShift Operator:
      Tables: staging_events, staging_songs
   C. Loading the Fact Table using the LoadFactOperator
      Table : songplays
   D. Loading the Dimension Table using the LoadDimensionOperator
      Tables : artists, songs, users, time
   E. Performing Data Quality checks on the following tables:
      songplays, songs, artists, users, time
   F. Executing the Dag as per the dependencies
      1. starting operation, 2a. loading staging_events, 2b. loading staging_songs, 
      3. loading fact table songplays, 4a. loading dimension table songs,
      4b.loading dimension table artists, 4c. loading dimension table users, 
      5. running data quality checks, 6. ending operation    
   
   @author: Diana Aranha
   Date:    July 7, 2021
"""

"""
   The DAG does not have past dependencies, tasks are retried 3 times on failure,
   and retries happen every 5 minutes, catchup is turned off, and 
   we do not email on retry
"""
default_args = {
    'owner': 'diana',
    'start_date': datetime(2021, 5, 1),
    'depends_on_past': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'email_on_retry': False
}

dag = DAG('udac_example_dag',
          default_args=default_args,
          description='Extract, Load and Transform Sparkify log and song data from S3 to Redshift with Airflow',
          schedule_interval='@hourly',
          catchup=False        
)

start_operator = DummyOperator(task_id='Begin_execution',  dag=dag)

# Load tables to AWS Redshift
# Load the staging table : staging_events
stage_events_to_redshift = StageToRedshiftOperator(
    task_id='Stage_events',
    dag=dag,
    table='staging_events',
    redshift_conn_id='redshift',
    aws_credentials_id='aws_credentials',     
    s3_bucket="udacity-dend",
    s3_key="log_data",    
    file_path='s3://udacity-dend/log_data',    
    copy_params="FORMAT AS JSON 's3://udacity-dend/log_json_path.json'",
    region="us-west-2"
)

# Load the staging table : staging_songs
stage_songs_to_redshift = StageToRedshiftOperator(
    task_id='Stage_songs',
    dag=dag,    
    table='staging_songs',
    redshift_conn_id='redshift',
    aws_credentials_id='aws_credentials',
    s3_bucket="udacity-dend",
    s3_key="song_data",    
    file_path='s3://udacity-dend/song_data/A/A/A',
    copy_params="FORMAT AS JSON 'auto'", 
    region="us-west-2"
)

# Loading the Fact Table -- songplays
load_songplays_table = LoadFactOperator(
    task_id='Load_songplays_fact_table',
    dag=dag,
    table='songplays',
    redshift_conn_id='redshift',
    select_sql=SqlQueries.songplays_table_insert,
)

# Loading the Dimension table -- users
load_users_dimension_table = LoadDimensionOperator(
    task_id='Load_users_dim_table',
    dag=dag,
    table='users2',
    redshift_conn_id='redshift',
    select_sql=SqlQueries.users_table_insert,
    table_mode='truncate'
)

# Loading the Dimension table -- songs
load_songs_dimension_table = LoadDimensionOperator(
    task_id='Load_songs_dim_table',
    dag=dag,
    table='songs',
    redshift_conn_id='redshift',
    select_sql=SqlQueries.songs_table_insert,
    table_mode='truncate'
)

# Loading the Dimension table -- artists
load_artists_dimension_table = LoadDimensionOperator(
    task_id='Load_artists_dim_table',
    dag=dag,
    table='artists',
    redshift_conn_id='redshift',
    select_sql=SqlQueries.artists_table_insert,
    table_mode='truncate'
)

# Loading the Dimension table -- time
load_time_dimension_table = LoadDimensionOperator(
    task_id='Load_time_dim_table',
    dag=dag,
    table='time',
    redshift_conn_id='redshift',
    select_sql=SqlQueries.time_table_insert,
    table_mode='truncate'
)

# Data Quality checks
data_quality_checks = [
    {'check_sql':'SELECT COUNT(*) FROM songplays WHERE playid IS NULL', 'expected_result': 0},
    {'check_sql':'SELECT COUNT(*) FROM songs WHERE songid IS NULL', 'expected_result': 0},
    {'check_sql':'SELECT COUNT(*) FROM artists WHERE artistid IS NULL', 'expected_result':0},
    {'check_sql':'SELECT COUNT(*) FROM users2 WHERE userid IS NULL', 'expected_result': 0},
    {'check_sql':'SELECT COUNT(*) FROM time WHERE start_time IS NULL', 'expected_result': 0}
]

run_quality_checks = DataQualityOperator(
    task_id='Run_data_quality_checks',
    list_of_tables=['songplays','songs', 'artists', 'users2', 'time'],
    data_quality_checks=data_quality_checks,
    redshift_conn_id='redshift',
    dag=dag,    
)

end_operator = DummyOperator(task_id='Stop_execution',  dag=dag)

# DAG dependencies
# Step 1: Creation of tables follows the task 'Begin_Execution'
start_operator >> stage_events_to_redshift
start_operator >> stage_songs_to_redshift

# stage_events and stage_songs must precede the loading of songplays_table
stage_events_to_redshift >> load_songplays_table
stage_songs_to_redshift  >> load_songplays_table

# loading songplays table has precedence over loading the dimension tables
load_songplays_table >> load_songs_dimension_table
load_songplays_table >> load_users_dimension_table
load_songplays_table >> load_artists_dimension_table
load_songplays_table >> load_time_dimension_table

# loading the 4 dimension tables has precedence over running data quality checks
load_songs_dimension_table >> run_quality_checks
load_users_dimension_table >> run_quality_checks
load_artists_dimension_table >> run_quality_checks
load_time_dimension_table >> run_quality_checks

run_quality_checks >> end_operator
