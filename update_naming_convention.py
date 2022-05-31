import sys
import boto3
import colored
from colored import stylize

 
def get_metric_alarms_by_prefix(client, prefix:str) -> list:
  alarms = client.describe_alarms(AlarmNamePrefix=prefix)
  return alarms.get("MetricAlarms", [])

def rename_metric_alarm(client, alarm:str, new_name:str) -> None:
  old_alarm_name = alarm["AlarmName"]
  alarm["AlarmName"] = new_name
  try:
    client.put_metric_alarm(**alarm)
  except:
    raise Exception("Errors are bad")(f"unable to create replacment alarm {new_name}")
  try:
    client.delete_alarms(AlarmNames=[old_alarm_name])
  except:
    raise Exception(f"unable to delete alarm: {old_alarm_name}")

  
def read_arguments() -> dict[str, str]:
  if(len(sys.argv)) < 5 or len(sys.argv) > 5 :
    print(stylize("\nusage: python3 update_naming_convention.py [prefix] [region] [current] [desired]", colored.fg("red")))
    exit()
  else:
    return sys.argv[1:]


if __name__ == '__main__':
  prefix, region, current, desired = read_arguments()
  client = boto3.client('cloudwatch', region_name=region)
  
  for alarm in get_metric_alarms_by_prefix(client, prefix):
    name_split = alarm["AlarmName"].split('-') 
    for count, value in enumerate(name_split):
      if value == current:
        name_split[count] = desired
        new_name = '-'.join(name_split)
        rename_metric_alarm(client, alarm, new_name)