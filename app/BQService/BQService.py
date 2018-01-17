from google.cloud import bigquery
import logging

# Instantiate BQ client under project xy-private
client = bigquery.Client()


def get_sql(id):
    return """
    SELECT Name, IF(RecordTypeId = '012b00000000ElpAAE', 'Customer', 'Supplier') AS AccountType, ShippingState AS Location
    FROM [bi-tables:Salesforce.Account]
    WHERE Id = '{}'
    """.format(id)


def run_query(id,client):
    sql = get_sql(id)
    config = bigquery.QueryJobConfig()
    config.use_legacy_sql = True
    job = client.query(sql, job_config = config)
    results = job.result()
    return results

# Main function to be exported to app
# Returns data in a python dictionary, which is a pseudo JSON format
def get_data(id):
    result_table = run_query(id,client)
    header = list(map(lambda x:x.name, result_table.schema))
    values = list(map(lambda x: list(x), result_table))[0]

    data = {}
    for i in range(len(header)):
        data[header[i]] = values[i]
    return data



