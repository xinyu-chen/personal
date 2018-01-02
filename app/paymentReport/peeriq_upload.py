import datetime as dt
import logging

from google.cloud import bigquery
from google.cloud import storage
from oauth2client.client import GoogleCredentials

download_folder = '/opt/behalf/cto/reporting/data'

def get_sql(date):
    query = """SELECT *, CASE WHEN LoanStatus='Charged Off' THEN PrincipalOutstanding Else 0 END as NetLoss,CASE WHEN LoanStatus='Charged Off' THEN ROUND(DefaultAmount-PrincipalOutstanding,2) ELSE 0 END as Recoveries   
        FROM (   
        SELECT ID as LoanID, 'Not Funded' as FundingStatus, CASE WHEN Is_Finwise IS FALSE THEN 'MCA' ELSE 'Loan' END as TrxType,  
        CASE WHEN Is_Finwise IS TRUE then 1 ELSE 0 END as PctFW, Payout_Method as PayoutMethod, AccountID as CustomerID, CASE WHEN trxs.CustomerFICO>900 THEN null ELSE trxs.CustomerFICO END as CustomerFICO,  
        CreditLimit, trxs.CustomerState as CustomerState, 0 AS BusinessAge, 
        CASE WHEN acct.CLOED is not null AND acct.Credit_Limit >100000 THEN Date_ADD(acct.CLOED,-6,'MONTH')  
             WHEN acct.CLOED is not null AND acct.Credit_Limit BETWEEN 50000 AND 100000 THEN Date_ADD(acct.CLOED,-12,'MONTH') ELSE null END as LastReUW,  
        Supplier_Name as SupplierName,Supplier_Industry as SupplierIndustry,   
        CASE WHEN Payout_Date is not null THEN DATE(Payout_Date) ELSE DATE(Payout_Hit_Date_New) END as PayoutDate, Date(First_repayment_date) as FirstRepaymentDate, Date(pmts.Next_Debit_date) As NextRepaymentDate,   
        Date(Last_AR_Date) as LastRepaymentDate, DATE(ORGLRDate) as OrigLastRepaymentDate,  
        Num_Days as Term, Repayment_Frequency as Product,  NARep as PlannedRepayments, Num_Repayments as OrigPlannedRepayments, nsRep as SettledRepayments, round(Total_Amount_To_Collect_Without_Fees/Num_Repayments,2) as RepaymentAmount,   
        ROUND(100*(Total_Customer_Fees)/(Amount*Num_Days/30),2) as TrxMPR,   
        Amount,Total_Paid_Out_To_Supplier as PayoutAmount,   
        Total_Customer_Fees as CustomerInterest,FinFee+Collection_Fees+CC_Fees as CustomerFees,Total_Supplier_Fees as SupplierFees,   
        CASE WHEN ROUND((Total_Received-Total_Paid_Out_To_Customer)*Amount/(Amount+Total_Customer_Fees),2)>Amount THEN Amount   
             ELSE ROUND((Gross_Total_Received_From_Customer-Total_Paid_Out_To_Customer)*Amount/(Amount+Total_Customer_Fees),2)   
                  + (CASE WHEN Amount>=Total_Paid_Out_To_Supplier THEN Total_Received_From_Supplier ELSE 0 END) END as PrincipalPaidToDate,   
        CASE WHEN ROUND((Total_Received-Total_Paid_Out_To_Customer)*(1-Amount/(Amount+Total_Customer_Fees)),2)>Total_Customer_Fees THEN Total_Customer_Fees   
             ELSE ROUND((Gross_Total_Received_From_Customer-Total_Paid_Out_To_Customer)*(1-Amount/(Amount+Total_Customer_Fees)),2) END    
             as InterestPaidToDate,   
        CASE WHEN ROUND((Total_Received-Total_Paid_Out_To_Customer)*(1-Amount/(Amount+Total_Customer_Fees)),2)<0   
             THEN Amount+Total_Customer_Fees+FinFee+Collection_Fees+CC_Fees-Total_Received_From_Customer-Total_Paid_Out_To_Customer   
             ELSE 0 END as CustomerFeesPaidToDate,   
        CASE WHEN Total_Received_From_Supplier+IFNULL(Credit_Note,0)>=Total_Paid_Out_To_Supplier THEN 0   
             WHEN Amount-(Total_Received-Total_Paid_Out_To_Customer)*Amount/(Amount+Total_Customer_Fees)<1 AND Amount>=Total_Paid_Out_To_Supplier THEN 0   
             ELSE ROUND(Amount-(CASE WHEN Amount>=Total_Paid_Out_To_Supplier THEN Total_Received_From_Supplier ELSE 0 END)   
                              -(Total_Received_From_Customer-Total_Paid_Out_To_Customer+Vendor_Refund)*(Amount/(Amount+Total_Customer_Fees)),2) END as PrincipalOutstanding,   
        CASE WHEN Total_Received_From_Supplier+IFNULL(Credit_Note,0)>=Total_Paid_Out_To_Supplier THEN 0   
             WHEN ROUND(Total_Customer_Fees-(Gross_Total_Received_From_Customer-Total_Paid_Out_To_Customer)*(1-Amount/(Amount+Total_Customer_Fees)),2)<0 THEN 0   
             ELSE ROUND(Total_Customer_Fees-(Gross_Total_Received_From_Customer-Total_Paid_Out_To_Customer)*(1-Amount/(Amount+Total_Customer_Fees)),2) END as InterestOutstanding,   
        CASE WHEN FinFee+Collection_Fees+CC_Fees=0 THEN 0   
             WHEN Total_Received_From_Supplier+IFNULL(Credit_Note,0)>=Total_Paid_Out_To_Supplier THEN 0   
             WHEN ROUND(Total_Customer_Fees-(Gross_Total_Received_From_Customer-Total_Paid_Out_To_Customer)*(1-Amount/(Amount+Total_Customer_Fees)),2)<0 THEN   
                  ROUND(Amount+FinFee+Collection_Fees+CC_Fees+Total_Customer_Fees-Total_Received-Total_Paid_Out_To_Customer,2)   
             ELSE ROUND(FinFee+Collection_Fees+CC_Fees,2) END as CustomerFeesOutstanding,   
        CASE WHEN Total_Received_From_Supplier+IFNULL(Credit_Note,0)>=Total_Paid_Out_To_Supplier THEN 'Principal Paid Up'   
             WHEN Amount-(Total_Received-Total_Paid_Out_To_Customer)*Amount/(Amount+Total_Customer_Fees)<1 AND Late_Bucket_181d_turn_over is null THEN 'Principal Paid Up'   
             WHEN Late_Bucket_181D_Turn_Over IS NULL AND Late_Bucket='Principal Paid Up' AND (Aging_Current_Future>0 OR date(Last_Ar_Date)>=current_date()) THEN 'Current'   
             WHEN Late_Bucket_181D_Turn_Over IS NULL AND Late_Bucket='Principal Paid Up' AND (Aging_more_120_Days>0 OR ROUND(Amount-(Total_Received-Total_Paid_Out_To_Customer)*(Amount/(Amount+Total_Customer_Fees)),2)>1   
             ) AND Aging_Current_Future=0 THEN 'Charged Off'   
             WHEN Late_Bucket_181D_Turn_Over IS NULL THEN Late_Bucket WHEN Late_Bucket IS NULL THEN 'Current'   
             ELSE 'Charged Off' END as LoanStatus,   
        Late_Bucket_Num_Days as DaysOverdue,   
        CASE WHEN Total_Received_From_Supplier+IFNULL(Credit_Note,0)>=Total_Paid_Out_To_Supplier THEN 0   
             WHEN Late_Bucket_181D_Turn_Over IS NULL AND Late_Bucket='Principal Paid Up' AND (Aging_Current_Future>0 OR date(Last_Ar_Date)>=current_date()) THEN 0   
             WHEN (Late_Bucket_181D_Turn_Over IS NOT NULL) AND (Amount-(Total_Received-Total_Paid_Out_To_Customer)*Amount/(Amount+Total_Customer_Fees)) > Late_bucket_181D_Turn_Over_Amount   
             THEN ROUND(Amount-Total_Received_From_Supplier-(Gross_Total_Received_From_Customer-Total_Paid_Out_To_Customer)*Amount/(Amount+Total_Customer_Fees),2)   
             WHEN (Late_Bucket_181D_Turn_Over IS NOT NULL) AND (Amount-(Total_Received-Total_Paid_Out_To_Customer)*Amount/(Amount+Total_Customer_Fees)) <= Late_bucket_181D_Turn_Over_Amount   
             THEN ROUND(Amount-(Total_Paid_Out_To_Supplier-Late_Bucket_181D_Turn_Over_Amount)*Amount/(Amount+Total_Customer_Fees),2)   
             WHEN Late_Bucket='Principal Paid Up' AND ROUND(Amount-(Total_Received-Total_Paid_Out_To_Customer)*Amount/(Amount+Total_Customer_Fees),2)>1   
             THEN ROUND(Amount-Total_Received_From_Supplier-(Gross_Total_Received_From_Customer-Total_Paid_Out_To_Customer)*Amount/(Amount+Total_Customer_Fees),2)   
             ELSE 0 END as DefaultAmount,Late_Bucket_181D_Turn_Over as ChargeOffDate   
             FROM [sf-backup-973:"""+date+""".Opportunity] as opp   
        JOIN [bi-tables:CustomizedTables.TrxsRawExtended] as trxs   
        ON trxs.TrxId=opp.ID   
        JOIN (SELECT ID as AcctID, CLOED, Credit_Limit FROM [sf-backup-973:"""+date+""".Account] ) as acct 
        ON trxs.CustomerID=acct.AcctID 
        LEFT JOIN (
        SELECT Trx, MIN(Hit_Date) as Next_Debit_Date FROM [sf-backup-973:"""+date+""".Payment] 
        WHERE RecordTypeID='012b00000000HbwAAE' 
        AND (Status='Halted Manually' OR Status='Halted Automatically' OR Status='Waiting for Scheduling' OR Status='In Process')
        GROUP BY 1
        ) as pmts
        ON trxs.TrxID=pmts.Trx
        WHERE Valid_For_Stats_extended is true AND Live_Status<>'Cancelled By Zazma' AND Live_Status<>'Cancelled By Supplier' AND Live_Status<>'Cancelled By Customer'   
        ) WHERE PayoutDate is not null AND PayoutAmount>0  
        ORDER BY PayoutDate DESC"""
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



