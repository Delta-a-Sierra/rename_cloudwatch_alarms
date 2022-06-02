"""
Description:
  This script is used to update the name of all cloudwatch metric alarms that have a given prefix within a region to a lowecase value.

Usage:
  python3 make_alarms_lowercase.py [prefix] [region]  

Example:
  python3 make_alarms_lowercase.py contoso eu-west-2
  changes:  contoso-dev-SERVER01-cpu-high -> contoso-dev-server01-cpu-high
"""
import boto3, logging, argparse


def get_metric_alarms_by_prefix(client: object, prefix: str) -> list:
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


def rename_metric_alarm_lowercase(client: object, alarm: str) -> None:
    """
    Creates a clone of the given alarm with a lowercase name then deletes the old alarm.
    """
    try:
        client.put_metric_alarm(
            AlarmName=(alarm["AlarmName"].lower()),
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
        logging.info(f"created replacement alarm {alarm['AlarmName'].lower()}")
    except Exception as error:
        logging.error(
            f"unable to create replacment alarm {alarm['AlarmName'].lower()}. error: {error}"
        )
        raise
    try:
        client.delete_alarms(AlarmNames=[alarm["AlarmName"]])
        logging.info(f"deleted alarm with uppercase name {alarm['AlarmName']}")
    except Exception as error:
        logging.error(f"unable to delete alarm: {alarm['AlarmName']}. error: {error}")
        raise


if __name__ == "__main__":
    # setting up logger
    logging.basicConfig(
        filename="make_alarms_lowercase.log",
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    # setting up cmd line argument parse
    parser = argparse.ArgumentParser(
        description="This script is used to update the name of all cloudwatch alarms\
            that have a given prefix within a region to a lowecase value."
    )
    parser.add_argument(
        "prefix", type=str, help="A prefix to match against when selecting alarms"
    )
    parser.add_argument(
        "region", type=str, help="The region the CloudWatch alarms reside in"
    )
    args = parser.parse_args()

    client = boto3.client("cloudwatch", region_name=args.region)

    # Gather alarms and seperates out the uppercase alarms
    uppercase_alarms = [
        alarm
        for alarm in get_metric_alarms_by_prefix(client, args.prefix)
        if alarm["AlarmName"] != alarm["AlarmName"].lower()
    ]

    # exits script if no uppercase alarms are found
    if len(uppercase_alarms) == 0:
        print("No uppercase alarms to modify")
        logging.info("No uppercase alarms to modify")
        exit()

    # Display alarms and request confirmation before continuing script
    for alarm in uppercase_alarms:
        print(alarm["AlarmName"])
    confirmation = input(
        f"Rename above ({len(uppercase_alarms)}) alarms to lowercase? (y/n): "
    ).lower()
    while confirmation not in ["y", "n"]:
        print("invalid choice")
        confirmation = input(
            f"Rename above ({len(uppercase_alarms)}) alarms to lowercase? (y/n): "
        ).lower()

    # Rename each alarm to its lowercase version
    if confirmation == "y":
        for alarm in uppercase_alarms:
            rename_metric_alarm_lowercase(client, alarm)
