import datetime as dt
import logging

from google.cloud import bigquery
from google.cloud import storage
from oauth2client.client import GoogleCredentials

download_folder = '/opt/behalf/cto/reporting/data'

def get_sql(date):
    query = """SELECT *, CASE WHEN LoanStatus='Charged Off' THEN PrincipalOutstanding Else 0 END as NetLoss,
    CASE WHEN LoanStatus='Charged Off' THEN GREATEST(ROUND(DefaultAmount-PrincipalOutstanding,2),0) ELSE 0 END as Recoveries   
    FROM (   
         SELECT ID as LoanID, CASE WHEN Is_Trx_Eligible_for_Debt_Facility is true THEN 'Eligible' ELSE 'Ineligible' END as EligibilityStatus,
         Debt_Facility_Funding_Status as FundingStatus, CASE WHEN Is_Finwise IS FALSE THEN 'MCA' ELSE 'Loan' END as TrxType,  
         CASE WHEN Is_Finwise IS TRUE then 1 ELSE 0 END as PctFW, Payout_Method as PayoutMethod, AccountID as CustomerID, 
         CASE WHEN trxs.CustomerFICO>900 THEN null ELSE trxs.CustomerFICO END as CustomerFICO,  
         CreditLimit, trxs.CustomerState as CustomerState, 0 AS BusinessAge, 
         CASE WHEN (CASE WHEN Payout_Date is not null THEN DATE(Payout_Date) ELSE DATE(Payout_Hit_Date_New) END)>=DATE(uw.FirstManualUWDate) THEN true ELSE false END as ManualUW, 
         CASE WHEN acct.CLOED is not null AND acct.Credit_Limit >100000 THEN Date_ADD(acct.CLOED,-6,'MONTH')  
              WHEN acct.CLOED is not null AND acct.Credit_Limit BETWEEN 50000 AND 100000 THEN Date_ADD(acct.CLOED,-12,'MONTH') ELSE null END as LastReUW, 
         uw.Annual_Revenue as AnnualRev, Supplier_Name as SupplierName,Supplier_Industry as SupplierIndustry,   
         CASE WHEN Payout_Date is not null THEN DATE(Payout_Date) ELSE DATE(Payout_Hit_Date_New) END as PayoutDate, 
         Date(First_repayment_date) as FirstRepaymentDate, Date(pmts.Next_Debit_date) As NextRepaymentDate,   
         Date(Last_AR_Date) as LastRepaymentDate, Is_Restructured as Restructured, DATE(ORGLRDate) as OrigLastRepaymentDate,  
         Num_Days as Term, Repayment_Frequency as Product, Num_Repayments as OrigPlannedRepayments, NARep as PlannedRepayments, nsRep as SettledRepayments, 
         ROUND((Amount+Total_Customer_Fees+FinFee)/(CASE WHEN NARep=0 THEN Num_Repayments ELSE NARep END),2) as RepaymentAmount,   
         ROUND(100*(Total_Customer_Fees+FinFee)/(Amount*Num_Days/30),2) as TrxMPR,   
         Amount,Total_Paid_Out_To_Supplier as PayoutAmount, Total_Customer_Fees+FinFee as CustomerInterest,ROUND(Collection_Fees+CC_Fees,2) as CustomerFees,
         Total_Supplier_Fees as SupplierFees, ROUND(POPA,2) as PrincipalPaidToDate, ROUND(POIA,2) as InterestPaidToDate,   
         CASE WHEN Collection_Fees+CC_Fees>0 
              THEN ROUND(Gross_Total_Received_From_Customer+Total_Received_From_Supplier+Total_Repayments_In_Process-POPA-POIA,2)
              ELSE 0 END as CustomerFeesPaidToDate,
         ROUND(NPOPA,2) as PrincipalOutstanding, ROUND(Total_Customer_Fees+FinFee-POIA,2) as InterestOutstanding,
         CASE WHEN Collection_Fees+CC_Fees>0 
              THEN ROUND(Collection_Fees+CC_Fees-(Gross_Total_Received_From_Customer+Total_Received_From_Supplier+Total_Repayments_In_Process-POPA-POIA),2)
              ELSE 0 END as CustomerFeesOutstanding, 
         CASE WHEN Late_Bucket_181D_Turn_Over is not null THEN 'Charged Off'
              WHEN NPOPA<=0 THEN 'Principal Paid Up'   
              WHEN Late_Bucket IS NULL THEN 'Current' 
              WHEN Late_Bucket_181D_Turn_Over IS NULL THEN Late_Bucket   
              ELSE 'Charged Off' END as LoanStatus,   
         Late_Bucket_Num_Days as DaysOverdue, Late_Bucket_181D_Turn_over_Amount as DefaultAmount,Late_Bucket_181D_Turn_Over as ChargeOffDate   
         FROM [bi-tables:Salesforce.Opportunity] as opp   
         JOIN [bi-tables:CustomizedTables.TrxsRawExtended] as trxs  
         ON trxs.TrxId=opp.ID   
         JOIN (SELECT ID as AcctID, CLOED, Credit_Limit FROM [bi-tables:Salesforce.Account]) as acct 
         ON trxs.CustomerID=acct.AcctID 
         LEFT JOIN (  
              SELECT Account,MIN(CreatedDate) as FirstManualUWDate, LAST(Annual_Revenue) as Annual_Revenue   
              FROM [zazma.com:beaming-storm-829:salesforce.Risk_Financials]   
              WHERE Risk_Decision='Approved' GROUP BY 1  
         ) as uw ON opp.AccountID=uw.Account  
         LEFT JOIN ( 
              SELECT Trx, MIN(Hit_Date) as Next_Debit_Date 
              FROM [bi-tables:Salesforce.Payment] 
              WHERE RecordTypeID='012b00000000HbwAAE' AND (Status='Waiting for Scheduling' OR Status='In Process') GROUP BY 1 
         ) as pmts 
         ON trxs.TrxID=pmts.Trx 
         WHERE Valid_For_Stats_extended is true AND Live_Status<>'Cancelled By Zazma' AND Live_Status<>'Cancelled By Supplier' AND Live_Status<>'Cancelled By Customer'
    ) WHERE PayoutDate is not null AND PayoutAmount>0
    ORDER BY PayoutDate DESC, LoanID DESC"""
    return query

def create_table(date, dataset_id, table_id):
    dataset_ref = xy_client.dataset(dataset_id)
    table_ref = dataset_ref.table(table_id)
    return table_ref

def run_query(date, client):
    sql = get_sql(today)
    config = bigquery.QueryJobConfig()
    config.use_legacy_sql = True
    result_table = create_table(date, xy_dataset_id, loan_tape_name)
    config.destination = result_table
    job = client.query(sql, job_config = config)
    result = job.result()
    return result_table

def export_data_to_gcs(table_ref, destination):
    job = xy_client.extract_table(table_ref, destination)
    job.result()

def dl_from_gcs(project_id, bucket_name, file_name):
    gcs = storage.Client(project=project_id)
    blob = gcs.bucket(bucket_name).get_blob(file_name)
    with open(file_name, 'wb') as file:
        blob.download_to_file(file)
    


# Download both from GCS
def download_file(file_name):
    dl_from_gcs('xy-private', bucket_name, file_name)


def uploadXml():
    logging.info('uploadXml')
    credentials = GoogleCredentials.get_application_default()

    # Project under sf-backup
    client = bigquery.Client()
    # Project under xy-private
    xy_client = bigquery.Client(project='xy-private')

    # Set-ups
    today = dt.datetime.today().strftime('%Y_%m_%d')

    xy_dataset_id = 'peeriq'
    gcs_project = 'xy-private'
    bucket_name = 'xml_upload'
    loan_tape_name = 'lt_'+today
    payment_name = 'p_'+today

    # Save both files to GCS
    p_dataset_ref = client.dataset(today)
    p_table_ref = p_dataset_ref.table('Payment')
    p_destination = 'gs://xml_upload/' + payment_name + '.csv'
    export_data_to_gcs(p_table_ref, p_destination)

    lt_table_ref = run_query(today, client)
    lt_destination = 'gs://xml_upload/' + loan_tape_name + '.csv'
    export_data_to_gcs(lt_table_ref, lt_destination)

    download_file(loan_tape_name + '.csv')
    download_file(payment_name + '.csv')



