import sys
import boto3
import colored
from colored import stylize

 
def get_metric_alarms_by_prefix(prefix:str, region:str) -> list:
  client = boto3.client('cloudwatch', region_name=region)
  alarms = client.describe_alarms(AlarmNamePrefix=prefix)
  return alarms.get("MetricAlarms", [])

def rename_metric_alarm_lowercase(alarm:str, region:str) -> None:
  client = boto3.client('cloudwatch', region_name=region)

  client.put_metric_alarm( # creates new alarm with correct name
    AlarmName=((alarm['AlarmName']).lower()),
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
  client.delete_alarms(AlarmNames=[alarm['AlarmName']]) # delets alarm with name in caps

def read_arguments() -> dict[str, str]:
  if(len(sys.argv)) < 3 or len(sys.argv) > 3 :
    print(stylize("\nusage: python3 make_alarms_lowercase.py [prefix] [region]", colored.fg("red")))
    exit()
  else:
    prefix = sys.argv[1]
    region = sys.argv[2]
    return {prefix: prefix, region: region}


if __name__ == '__main__':
  prefix, region = read_arguments()
  for alarm in get_metric_alarms_by_prefix(prefix, region):
    alarm_name_lower = alarm["AlarmName"].lower()
    if alarm["AlarmName"] != alarm_name_lower: 
      rename_metric_alarm_lowercase(alarm, region)

