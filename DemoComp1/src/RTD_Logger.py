import snap7
import time
import os
from datetime import datetime
import boto3
from botocore.config import Config
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RTDDataLogger:
    def __init__(self):
        """Initialize PLC and AWS connections with environment variables"""
        # Fetch configuration from environment variables
        self.plc_ip = os.getenv('PLC_IP', '192.168.0.1')
        self.rack = int(os.getenv('PLC_RACK', 0))
        self.slot = int(os.getenv('PLC_SLOT', 1))
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        self.database_name = os.getenv('DATABASE_NAME', 'TestingDatabase')
        self.table_name = os.getenv('TABLE_NAME', 'TestingTable')
        
        # AWS Timestream setup
        config = Config(
            read_timeout=20,
            max_pool_connections=5000,
            retries=dict(max_attempts=10)
        )
        self.write_client = boto3.client(
            'timestream-write',
            region_name=self.aws_region,
            config=config
        )
        
        # PLC setup
        self.plc = snap7.client.Client()

    def connect_plc(self):
        """Establish connection to the PLC"""
        try:
            self.plc.connect(self.plc_ip, self.rack, self.slot)
            logger.info(f"Connected to PLC at {self.plc_ip}")
            return True
        except Exception as e:
            logger.error(f"PLC connection error: {e}")
            return False
            
    def read_rtd(self):
        """Read RTD value from the PLC"""
        try:
            # Read from DB1, starting from byte 0, length 4 bytes (REAL/FLOAT)
            data = self.plc.db_read(1, 0, 4)
            # Convert bytes to float (REAL)
            temp = snap7.util.get_real(data, 0)
            return temp
        except Exception as e:
            logger.error(f"Error reading RTD: {e}")
            return None
            
    def write_to_timestream(self, temperature):
        """Write temperature reading to AWS Timestream"""
        try:
            current_time = str(int(time.time() * 1000))  # Current time in milliseconds
            
            records = [{
                'Dimensions': [
                    {'Name': 'sensor_type', 'Value': 'RTD_TP100'},
                    {'Name': 'location', 'Value': 'PLC_1'},  # Customize as needed
                ],
                'MeasureName': 'temperature',
                'MeasureValue': str(temperature),
                'MeasureValueType': 'DOUBLE',
                'Time': current_time
            }]

            result = self.write_client.write_records(
                DatabaseName=self.database_name,
                TableName=self.table_name,
                Records=records,
                CommonAttributes={}
            )
            
            logger.info(f"Successfully wrote temperature {temperature}°C to Timestream")
            return True
            
        except self.write_client.exceptions.RejectedRecordsException as e:
            logger.error(f"Timestream write error (RejectedRecords): {e}")
            for rejected in e.response["RejectedRecords"]:
                logger.error(f"Rejected record: {rejected}")
            return False
            
        except Exception as e:
            logger.error(f"Timestream write error: {e}")
            return False
            
    def start_logging(self):
        """Start continuous logging with specified interval"""
        interval = int(os.getenv('LOGGING_INTERVAL', 5))  # Default interval is 5 seconds
        logger.info(f"Starting RTD data logging every {interval} seconds...")
        try:
            while True:
                temp = self.read_rtd()
                if temp is not None:
                    logger.info(f"Temperature reading: {temp}°C")
                    self.write_to_timestream(temp)
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("\nLogging stopped by user")
        finally:
            if self.plc.get_connected():
                self.plc.disconnect()
                logger.info("Disconnected from PLC")

if __name__ == "__main__":
    logger = RTDDataLogger()
    if logger.connect_plc():
        logger.start_logging()