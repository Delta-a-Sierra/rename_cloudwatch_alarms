import sys, boto3, logging, colored
from colored import stylize


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


def read_arguments() -> dict[str, str]:
    if (len(sys.argv)) < 5 or len(sys.argv) > 5:
        print(
            stylize(
                "\nusage: python3 update_naming_convention.py [prefix] [region] [current] [desired]",
                colored.fg("red"),
            )
        )
        exit()
    else:
        return sys.argv[1:]


if __name__ == "__main__":
    # setup
    logging.basicConfig(
        filename="update_naming_convention.log",
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    prefix, region, current, desired = read_arguments()
    client = boto3.client("cloudwatch", region_name=region)

    # gets alarms where current string is in its name
    changeable_alarms = [
        alarm
        for alarm in get_metric_alarms_by_prefix(client, prefix)
        if current in alarm["AlarmName"].split("-")
    ]
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
                if value == current:
                    name_split[count] = desired
            new_name = "-".join(name_split)
            rename_metric_alarm(client, alarm, new_name)
