from main import application

if __name__ == "__main__":
    logging.basicConfig(filename='/opt/behalf/cto/reporting/log/reporting.log', level=logging.INFO)
    application.run()