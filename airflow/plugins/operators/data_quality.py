"""
   The DataQualityOperator checks if data qulaity criteria are met
   More specifically, 
   For each of the dimension tables :
   a. if the primary key is null, an error message is displayed. 
   b. If data quality checks are successful, a success message is displayed
   
   @author: Diana Aranha
   Date:    July 7, 2021
"""

from airflow.hooks.postgres_hook import PostgresHook
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
import itertools

class DataQualityOperator(BaseOperator):

    ui_color = '#89DA59'

    @apply_defaults
    def __init__(self,
                 list_of_tables= [],
                 data_quality_checks= [],
                 redshift_conn_id = 'redshift',
                 *args, **kwargs):
        
        """
            Initializes variables for the data quality process
            Arguments:
              self : current object              
              redshift_conn_id : string
              data_quality_check : list 
              *args -- arguments
              **kwargs -- keyword arguments
        """
        
        super(DataQualityOperator, self).__init__(*args, **kwargs)
        self.redshift_conn_id = redshift_conn_id
        self.list_of_tables = list_of_tables
        self.data_quality_checks = data_quality_checks              

    def execute(self, context):
        """
           1. Gets called only during a DAG run.
           2. Executes the statements for the object denoted by self
              getting the values from the current context
           3. Uses redshift through the PostgresHook
         
           Arguments:
           self is the current instance or class object
           context contains context variables
        """
        if len(self.data_quality_checks) == 0:
            self.log.info('DataQualityOperator not implemented yet')
            return
        
        redshift_hook = PostgresHook(postgres_conn_id=self.redshift_conn_id) 
        
        errors = 0
        failure_tests = []

        # process each sql stmt for data quality relevant to each dimension table:
        # Dimension tables : a. songplays, b. songs, c. artists, d. users, e. time
       
        for (curr_table, check_stmt) in zip(self.list_of_tables, self.data_quality_checks):
            curr_sql = check_stmt.get('check_sql')
            result1 = check_stmt.get('expected_result')
            
            self.log.info('Current Table Processed : ' + curr_table)

            try:
                records = redshift_hook.get_records(curr_sql)[0]
            except Exception as e:
                self.loginfo(f"Error : {curr_table} : Query failed :  {e}")

            # record error when actual result is not the same as expected result
            if result1 != records[0]:
                errors += 1
                failure_tests.append(curr_table + ' : ' + curr_sql)
        
        # display Failure or Success Message     
        if errors > 0:
            self.log.info(failure_tests)
            self.log.info('Failure Msg : Tests Failed')
            raise ValueError('Error : Failed : Data Quality check')
        else:
            self.log.info('Success : All Data Quality Tests passed')