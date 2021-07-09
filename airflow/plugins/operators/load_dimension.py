"""
   The LoadDimensionOperator loads the dimension tables:
   a. songs, artist, users, time
   
   @author: Diana Aranha
   Date: July 7, 2021
"""
from airflow.hooks.postgres_hook import PostgresHook
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

class LoadDimensionOperator(BaseOperator):

    ui_color = '#80BD9E'

    @apply_defaults
    def __init__(self,
                 table,
                 redshift_conn_id='redshift',
                 select_sql='',
                 table_mode='',
                 *args, **kwargs):

        """
           Initializes variables for the fact table
           Arguments:
              self : current object
              table : the fact table
              redshift_conn_id : string
              select_sql : string
              mode : string
              *args -- arguments
              **kwargs -- keyword arguments
        """

        super(LoadDimensionOperator, self).__init__(*args, **kwargs)
        
        # initialize instance variables
        self.table            = table
        self.redshift_conn_id = redshift_conn_id
        self.select_sql       = select_sql
        self.table_mode       = table_mode

    def execute(self, context):
        """
           This method :
           1. Gets called only during a DAG run.
           2. Executes the statements for the object denoted by self
              getting the values from the current context
           3. Uses redshift through the PostgresHook
           4. Deletes data from the dimension table if the mode is 'truncate'
           4. Inserts data into the fact table

           Arguments:
           self is the current instance or class object
           context contains context variables
        """
        
        redshift_hook = PostgresHook("redshift")

        if self.table_mode == 'truncate':
            self.log.info(f'Deleting data from Dimension table : {self.table} ...')
            redshift_hook.run(f'DELETE FROM {self.table};')
            self.log.info("Deletion Status : Completed")

        sql = f"""
            INSERT INTO {self.table}
            {self.select_sql};
        """
                
        self.log.info(f'Begin Loading data into Dimension Table : {self.table} ...')
        redshift_hook.run(sql)
        self.log.info(" Dimension Table Status : Loading Completed")       
