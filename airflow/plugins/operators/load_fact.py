from airflow.hooks.postgres_hook import PostgresHook
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

"""
   The LoadFactOperator loads the songplays fact table
   @author : Diana Aranha
   Date : July 7, 2021
"""

class LoadFactOperator(BaseOperator):

    ui_color = '#F98866'

    @apply_defaults
    def __init__(self,
                 table,
                 redshift_conn_id = 'redshift',
                 select_sql='',
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

        super(LoadFactOperator, self).__init__(*args, **kwargs)
        
        # assign instance variables
        self.table = table
        self.redshift_conn_id = redshift_conn_id
        self.select_sql = select_sql

    def execute(self, context):
        """
           This method :
           1. Gets called only during a DAG run.
           2. Executes the statements for the object denoted by self
              getting the values from the current context
           3. Uses redshift through the PostgresHook
           4. Inserts data into the fact table

           Arguments:
           self is the current instance or class object
           context contains context variables
        """
        
        redshift_hook = PostgresHook("redshift")
        self.log.info(f'Start Loading Data into Fact Table : {self.table} ...')

        sql = f"""
            INSERT INTO {self.table}
            {self.select_sql};
        """

        # implement insertion stmt - to insert into fact table
        redshift_hook.run(sql)
        self.log.info("Loading Status - Fact Table : Completed")
