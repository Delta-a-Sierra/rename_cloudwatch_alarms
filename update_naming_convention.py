import sys
import boto3
import colored
from colored import stylize

 
def get_metric_alarms_by_prefix(prefix:str, region:str) -> list:
  client = boto3.client('cloudwatch', region_name=region)
  alarms = client.describe_alarms(AlarmNamePrefix=prefix)
  return alarms.get("MetricAlarms", [])

def rename_metric_alarm(alarm:str, new_name:str,region:str) -> None:
  client = boto3.client('cloudwatch', region_name=region)

  client.put_metric_alarm( # creates new alarm with correct name
    AlarmName=new_name,
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
  client.delete_alarms(AlarmNames=[alarm['AlarmName']]) # deletes alarm with old name

def read_arguments() -> dict[str, str]:
  if(len(sys.argv)) < 5 or len(sys.argv) > 5 :
    print(stylize("\nusage: python3 update_naming_convention.py [current] [desired]", colored.fg("red")))
    exit()
  else:
    prefix = sys.argv[1]
    region = sys.argv[2]
    current = sys.argv[3]
    desired = sys.argv[4]
    return {prefix: prefix, region: region, current: current, desired: desired}


if __name__ == '__main__':
  prefix, region, current, desired = read_arguments()
  for alarm in get_metric_alarms_by_prefix(prefix, region):
    name_split = alarm["AlarmName"].split('-') 
    for count, value in enumerate(name_split):
      if value == current:
        name_split[count] = desired
        new_name = '-'.join(name_split)
        rename_metric_alarm(alarm, new_name , region)

