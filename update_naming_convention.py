"""
Description:
  This script is used to update a section of all cloudwatch metric alarms that have a given prefix within a region.
  sections are deliminated by -

Usage:
  python3 update_naming_convention.py [prefix] [region] [current] [desired]  

Example:
  python3 update_naming_convention.py contoso eu-west-2 dev prod
  changes:  contoso-dev-server01-cpu-high -> contoso-prod-server01-cpu-high
"""

import argparse, boto3, logging
from ast import parse


def get_metric_alarms_by_prefix(client, prefix: str) -> list:
    """
    Gets all metric alarms that begin with the given prefix
    """
    try:
        alarms = client.describe_alarms(AlarmNamePrefix=prefix)
        logging.info(f"Gathered all alarms matching prefix: {prefix}")
        return alarms.get("MetricAlarms", [])
    except Exception as error:
        logging.error(f"Unable to gather alarms. error: {error}")
        raise


def rename_metric_alarm(client, alarm: str, new_name: str) -> None:
    """
    Creates a clone of the given alarm with an updated name then deletes the old alarm.
    """
    try:
        client.put_metric_alarm(
            AlarmName=new_name,
            ActionsEnabled=alarm["ActionsEnabled"],
            OKActions=alarm["OKActions"],
            AlarmActions=alarm["AlarmActions"],
            InsufficientDataActions=alarm["InsufficientDataActions"],
            MetricName=alarm["MetricName"],
            Namespace=alarm["Namespace"],
            Statistic=alarm["Statistic"],
            Dimensions=alarm["Dimensions"],
            Period=alarm["Period"],
            EvaluationPeriods=alarm["EvaluationPeriods"],
            Threshold=alarm["Threshold"],
            ComparisonOperator=alarm["ComparisonOperator"],
        )
        logging.info(f"created replacement alarm {new_name}")
    except Exception as error:
        logging.error(f"unable to create replacment alarm {new_name}. error: {error}")
        raise
    try:
        client.delete_alarms(AlarmNames=[alarm["AlarmName"]])
        logging.info(f"deleted old alarm with name {alarm['AlarmName']}")
    except Exception as error:
        logging.error(f"unable to delete alarm: {alarm['AlarmName']}. error: {error}")
        raise


if __name__ == "__main__":
    # setting up logger
    logging.basicConfig(
        filename="update_naming_convention.log",
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    # setting up cmd line argument parse
    parser = argparse.ArgumentParser(
        description="  This script is used to update a section of all cloudwatch metric alarms that have a given prefix\
        within a region. sections are deliminated by -"
    )
    parser.add_argument(
        "prefix", type=str, help="A prefix to match against when selecting alarms"
    )
    parser.add_argument(
        "region", type=str, help="The region the CloudWatch alarms reside in"
    )
    parser.add_argument("current", type=str, help="Value you wish to change")
    parser.add_argument("desired", type=str, help="The new value you desire")

    args = parser.parse_args()

    client = boto3.client("cloudwatch", region_name=args.region)

    # gets alarms where current string is in its name
    changeable_alarms = [
        alarm
        for alarm in get_metric_alarms_by_prefix(client, args.prefix)
        if args.current in alarm["AlarmName"].split("-")
    ]
    # exits script if no suitable alarms are found
    if len(changeable_alarms) == 0:
        print("No alarms to modify")
        logging.info("No alarms to modify")
        exit()

    # Display alarms and request confirmation before continuing script
    for alarm in changeable_alarms:
        print(alarm["AlarmName"])
    confirmation = input(
        f"Rename above ({len(changeable_alarms)}) alarms? (y/n): "
    ).lower()
    while confirmation not in ["y", "n"]:
        print("invalid choice")
        confirmation = input(
            f"Rename above ({len(changeable_alarms)}) alarms? (y/n): "
        ).lower()

    # splits the alarm up and replaces the section that match current var with what is desired then provides the new to the name rename function
    if confirmation == "y":
        for alarm in changeable_alarms:
            name_split = alarm["AlarmName"].split("-")
            for count, value in enumerate(name_split):
                if value == args.current:
                    name_split[count] = args.desired
            new_name = "-".join(name_split)
            rename_metric_alarm(client, alarm, new_name)
