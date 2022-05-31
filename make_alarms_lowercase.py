import sys
import boto3
import colored
from colored import stylize

 
def get_metric_alarms_by_prefix(client, prefix:str) -> list:
  alarms = client.describe_alarms(AlarmNamePrefix=prefix)
  return alarms.get("MetricAlarms", [])

def rename_metric_alarm_lowercase(client, alarm:str) -> None:
  created = False
  try:
    client.put_metric_alarm( 
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
    created = True
  except:
    print(f"unable to create replacment alarm {alarm['AlarmName'].lower()}")
    if created:
      try:
        client.delete_alarms(AlarmNames=[alarm['AlarmName']])
      except:
        print(f"unable to delete alarm: {alarm['AlarmName']}")


def read_arguments() -> dict[str, str]:
  if(len(sys.argv)) != 3 :
    print(stylize("\nusage: python3 make_alarms_lowercase.py [prefix] [region]", colored.fg("red")))
    exit()
  else:
    return sys.argv[1:]

if __name__ == '__main__':
  prefix, region = read_arguments()
  client = boto3.client('cloudwatch', region_name=region)

  for alarm in get_metric_alarms_by_prefix(client, prefix):
    alarm_name_lower = alarm["AlarmName"].lower()
    if alarm["AlarmName"] != alarm_name_lower: 
      rename_metric_alarm_lowercase(client, alarm)

