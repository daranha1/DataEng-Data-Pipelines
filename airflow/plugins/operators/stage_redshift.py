from airflow.hooks.postgres_hook import PostgresHook
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from airflow.contrib.hooks.aws_hook import AwsHook

"""
   The StageToRedshiftOperator loads the staging_events and staging_songs tables.
   1. loads staging_events from s3://udacity-dend/log_json_path.json from the region 'us-west-2'
   2. loads staging_songs from  s3://udacity-dend/song_data/A/A/A from the region 'us-west-2'
      staging_songs is formatted as JSON 'auto'
   
   @author: Diana Aranha
   Date:    July 7, 2021
"""

class StageToRedshiftOperator(BaseOperator):
    ui_color = '#358140'

    """
           Initializes variables
           Arguments:
              self : current object
              s3_bucket : string
              s3_prefix : string
              table : the fact table
              redshift_conn_id : string 
              aws_conn_id : the aws credentials
              *args -- arguments
              **kwargs -- keyword arguments
    """
      
    copy_stmt = """
                   COPY {}
                   FROM '{}'
                   ACCESS_KEY_ID '{}'
                   SECRET_ACCESS_KEY '{}'
                   REGION '{}'
                   COMPUPDATE OFF       
                   {}
              """
          
    @apply_defaults
    def __init__(self,   
                 table,    
                 redshift_conn_id="",
                 aws_credentials_id="",
                 s3_bucket="",
                 s3_key="",
                 file_path="",                 
                 copy_params="",
                 region="",               
                 *args, **kwargs): 
         super(StageToRedshiftOperator, self).__init__(*args, **kwargs)
          
         # initialize instance variables
         self.table               = table 
         self.redshift_conn_id    = redshift_conn_id
         self.aws_credentials_id  = aws_credentials_id               
         self.s3_bucket           = s3_bucket
         self.s3_key              = s3_key
         self.file_path           = file_path         
         self.copy_params         = copy_params
         self.region              = region         

    def execute(self, context):
        """
           This method :
           1. Gets called only during a DAG run.
           2. Executes the statements for the object denoted by self
              getting the values from the current context
           3. Uses redshift through the PostgresHook
           4. Loads data from the udacity-dend S3 bucket to staging tables in redshift
           Arguments:
              self : current object
              context : contains context variables
        """
        # assign credentials info
        aws_hook      = AwsHook(self.aws_credentials_id)
        credentials   = aws_hook.get_credentials()
        redshift_hook = PostgresHook(postgres_conn_id=self.redshift_conn_id)        

        self.log.info(f'Preparing to stage data from {self.s3_bucket}/{self.s3_key} to {self.table} table ...')
        redshift_hook.run("delete from {}".format(self.table))
        
        self.log.info(f'Copy data to staging tables : {self.table} ...')
        
        rendered_key = self.s3_key.format(**context)
        
        self.log.info('Rendered Key : ' + rendered_key)
        self.log.info( f'S3 bucket :  {self.s3_bucket}')
        
        s3_path="s3://{}/{}".format(self.s3_bucket, rendered_key)            
        
        self.log.info( f'self.table : {self.table}')       
        self.log.info( f'self.credentials.access_key : {credentials.access_key}')
               
        self.log.info( f'self.region : {self.region}')       
            
        self.log.info( f'file_path : {self.file_path}')
        self.log.info( f'self.copy_params : {self.copy_params}') 
            
        # load the parameters for the copy stmt
        sql_stmt = StageToRedshiftOperator.copy_stmt.format(
                        self.table,
                        self.file_path,
                        credentials.access_key,
                        credentials.secret_key,
                        self.region,
                        self.copy_params
        )       
      
        self.log.info('COPY Command Status : Started ...')
        redshift_hook.run(sql_stmt)
        self.log.info("COPY Command Status : Completed")