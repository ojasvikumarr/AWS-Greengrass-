import sys
import src.greeter as greeter
import snap7
import time
from datetime import datetime
import boto3
from botocore.config import Config

class RTDDataLogger:
    def __init__(self, plc_ip='192.168.0.1', rack=0, slot=1, 
                 aws_region='us-east-1',
                 database_name='TestingDatabase',
                 table_name='TestingTable'):
        """Initialize PLC and AWS connections"""
        # PLC setup
        self.plc = snap7.client.Client()
        self.plc_ip = plc_ip
        self.rack = rack
        self.slot = slot
        
        # AWS Timestream setup
        self.database_name = database_name
        self.table_name = table_name
        
        # Configure AWS client with retry configuration
        config = Config(
            read_timeout=20,
            max_pool_connections=5000,
            retries=dict(max_attempts=10)
        )
        
        # Initialize Timestream write client
        self.write_client = boto3.client(
            'timestream-write',
            region_name=aws_region,
            config=config
        )
        
    def connect_plc(self):
        """Establish connection to the PLC"""
        try:
            self.plc.connect(self.plc_ip, self.rack, self.slot)
            print(f"Connected to PLC at {self.plc_ip}")
            return True
        except Exception as e:
            print(f"PLC connection error: {e}")
            return False
            
    def read_rtd(self):
        """Read RTD value from the PLC
        Returns temperature in Celsius"""
        try:
            # Read from DB1, starting from byte 0, length 4 bytes (REAL/FLOAT)
            # Adjust DB number and byte offset according to your PLC program
            data = self.plc.db_read(1, 0, 4)
            # Convert bytes to float (REAL)
            temp = snap7.util.get_real(data, 0)
            return temp
        except Exception as e:
            print(f"Error reading RTD: {e}")
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
            
            print(f"Successfully wrote temperature {temperature}°C to Timestream")
            return True
            
        except self.write_client.exceptions.RejectedRecordsException as e:
            print(f"Timestream write error (RejectedRecords): {e}")
            for rejected in e.response["RejectedRecords"]:
                print(f"Rejected record: {rejected}")
            return False
            
        except Exception as e:
            print(f"Timestream write error: {e}")
            return False
            
    def start_logging(self, interval=1):
        """Start continuous logging with specified interval"""
        print("Starting RTD data logging to AWS Timestream...")
        try:
            while True:
                temp = self.read_rtd()
                if temp is not None:
                    print(f"Temperature reading: {temp}°C")
                    self.write_to_timestream(temp)
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nLogging stopped by user")
        finally:
            if self.plc.get_connected():
                self.plc.disconnect()
                print("Disconnected from PLC")

if __name__ == "__main__":
    # AWS and PLC Configuration
    AWS_REGION = 'us-east-1'  # Replace with your AWS region
    DATABASE_NAME = 'TestingDatabase'  # Replace with your database name
    TABLE_NAME = 'TestingTable'  # Replace with your table name
    PLC_IP = '192.168.0.1'  # Replace with your PLC's IP
    
    # Create logger instance
    logger = RTDDataLogger(
        plc_ip=PLC_IP,
        aws_region=AWS_REGION,
        database_name=DATABASE_NAME,
        table_name=TABLE_NAME
    )
    
    # Connect to PLC and start logging if connection successful
    if logger.connect_plc():
        # Start logging with 5 second interval
        logger.start_logging(interval=5)