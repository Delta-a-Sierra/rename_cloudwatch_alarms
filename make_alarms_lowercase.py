import sys

import boto3
import colored
import logging
from colored import stylize




def get_metric_alarms_by_prefix(client, prefix:str) -> list:
  try:
    alarms = client.describe_alarms(AlarmNamePrefix=prefix)
    logging.info(f'Gathered all alarms matching prefix: {prefix}')
    return alarms.get("MetricAlarms", [])
  except Exception as error:
    logging.error(f"Unable to gather alarms. error: {error}")
    exit()

def rename_metric_alarm_lowercase(client, alarm:str) -> None:
  try:
    client.put_metric_alarm(
      AlarmName=(alarm['AlarmName'].lower()),
      ActionsEnabled=alarm['ActionsEnabled'],
      OKActions=alarm['OKActions'],
      AlarmActions=alarm['AlarmActions'],
      InsufficientDataActions=alarm['InsufficientDataActions'],
      MetricName=alarm['MetricName'],
      Namespace=alarm['Namespace'],
      Statistic=alarm['Statistic'],
      Dimensions=alarm['Dimensions'],
      Period=alarm['Period'],
      EvaluationPeriods=alarm['EvaluationPeriods'],
      Threshold=alarm['Threshold'],
      ComparisonOperator=alarm['ComparisonOperator']
    )
  except:
    raise Exception(f"unable to create replacment alarm {alarm['AlarmName'].lower()}")
  try:
    client.delete_alarms(AlarmNames=[alarm['AlarmName']])
  except:
    raise Exception(f"unable to delete alarm: {alarm['AlarmName']}")

def read_arguments() -> dict[str, str]:
  if(len(sys.argv)) != 3 :
    print(stylize("\nusage: python3 make_alarms_lowercase.py [prefix] [region]", colored.fg("red")))
    exit()
  else:
    return sys.argv[1:]


if __name__ == '__main__':
  # setup
  logging.basicConfig(filename='make_alarms_lowecase.log', format='%(asctime)s - %(levelname)s - %(message)s')
  prefix, region = read_arguments()
  client = boto3.client('cloudwatch', region_name=region)

  # Gather alarms and seperates out the uppercase alarms
  uppercase_alarms = [alarm for alarm in get_metric_alarms_by_prefix(client, prefix) if alarm['AlarmName'] != alarm['AlarmName'].lower() ]

  # exits script if no uppercase alarms are found
  if len(uppercase_alarms) == 0:
    print('No uppercase alarms to modify')
    exit() 

  # Display alarms and request confirmation before continuing script 
  for alarm in uppercase_alarms:
    print(alarm['AlarmName']) 
  confirmation = input(f"Rename above ({len(uppercase_alarms)}) alarms to lowercase? (y/n): ").lower()
  while confirmation not in ['y', 'n']:
    print('invalid choice')
    confirmation = input(f"Rename above ({len(uppercase_alarms)}) alarms to lowercase? (y/n): ").lower()

  # Rename each alarm to its lowercase version 
  if confirmation == 'y':
    for alarm in uppercase_alarms:
      rename_metric_alarm_lowercase(client, alarm)

