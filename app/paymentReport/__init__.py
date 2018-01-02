import os
import sys

# find folder directory
direct = sys.argv[0].split('/')
direct = '/'.join(direct[:-1]) + "/paymentReport"

# Create credential as an environmental variable
json_key = direct + '/XY private-26235b64179e.json'
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = json_key





