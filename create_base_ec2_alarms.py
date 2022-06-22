from operator import itemgetter
import boto3, logging, argparse, csv


alarms = {
    "disk-usage-high": {
        "AlarmName": "",
        "ActionsEnabled": True,
        "OKActions": [],
        "AlarmActions": [],
        "InsufficientDataActions": [],
        "MetricName": "LogicalDisk % Free Space",
        "Namespace": "CWAgent",
        "Statistic": "Average",
        "Dimensions": [{"Name": "InstanceId", "Value": ""}],
        "Period": 900,
        "EvaluationPeriods": 1,
        "Threshold": 80.0,
        "ComparisonOperator": "GreaterThanOrEqualToThreshold",
    },
    "disk-d:-usage-high": {
        "AlarmName": "",
        "ActionsEnabled": True,
        "OKActions": [],
        "AlarmActions": [],
        "InsufficientDataActions": [],
        "MetricName": "LogicalDisk % Free Space",
        "Namespace": "CWAgent",
        "Statistic": "Average",
        "Dimensions": [
            {"Name": "InstanceId", "Value": ""},
            {"Name": "Instance", "Value": "d: "},
        ],
        "Period": 900,
        "EvaluationPeriods": 1,
        "Threshold": 80.0,
        "ComparisonOperator": "GreaterThanOrEqualToThreshold",
    },
    "ram-usage-high": {
        "AlarmName": "",
        "ActionsEnabled": True,
        "OKActions": [],
        "AlarmActions": [],
        "InsufficientDataActions": [],
        "MetricName": "Memory % Committed Bytes In Use",
        "Namespace": "CWAgent",
        "Statistic": "Average",
        "Dimensions": [{"Name": "InstanceId", "Value": ""}],
        "Period": 900,
        "EvaluationPeriods": 1,
        "Threshold": 80.0,
        "ComparisonOperator": "GreaterThanOrEqualToThreshold",
    },
}


def get_running_instances() -> list[dict]:
    ec2 = boto3.resource("ec2")
    instances = []
    for instance in ec2.instances.all():
        name = ""
        for tag in instance.tags:
            if tag["Key"] == "Name":
                name = tag["Value"]
        if instance.state["Name"] == "running":
            instances.append({"id": instance.id, "name": name})
    return sorted(instances, key=itemgetter("name"))


def create_alarm(name, instance_id, alarm, client) -> None:
    alarm["Dimensions"][0] = {"Name": "InstanceId", "Value": instance_id}
    alarm["AlarmName"] = name
    try:
        client.put_metric_alarm(**alarm)
        logging.info(f"created alarm {name}")
        print(f"created alarm {name}")
    except Exception as error:
        logging.error(f"unable to create alarm {name}. error: {error}")
        raise


def validate_list_entry(choice, list) -> bool:
    if choice == "a":
        return True
    for char in choice.split(","):
        try:
            char = int(char.strip())
        except ValueError:
            print(f"char: {char} is not a valid choice please use numbers or 'a'")
            return False
        if char not in [*range(0, len(list))] and type(char) == int:
            print(f"invalid choice: {char} please select an index from above list")
            return False
    return True


def shrink_to_choices(choice, list) -> list:
    temp = []
    # splits up the confirmation string and makes it usable as an index
    for index in [int(index.strip()) for index in choice.split(",")]:
        temp.append(list[index])
    return temp


def run_interactive(prefix) -> None:
    # Get instances
    instances = get_running_instances()

    # Print Instances out to terminal
    print("\nRunning Instances\n------------------")
    for index, instance in enumerate(instances):
        print(f"{index}: {instance['name']}, id: {instance['id']}")

    # Gets user inputs and validates it
    validated = False
    while not validated:
        confirmation = input(
            "\nplease select instance/instances to configure alarm for\n input comma-seperated list of correspoding indexes e.g '0,5,2' or 'a' for all instances\n - : "
        )
        validated = validate_list_entry(confirmation, instances)

    # shrinks instance variable down to only requested instances
    if confirmation != "a":
        instances = shrink_to_choices(confirmation, instances)

    # confirms choice instances
    confirmation = ""
    while confirmation not in ["Y", "y", "N", "n"]:
        print("\nConfirm Instances Choice\n--------------------------")
        for instance in instances:
            print(instance["name"])
        confirmation = input("\nenter 'y' or 'n' to confirm/deny: ")
    if confirmation in ["N", "n"]:
        exit()

    # Display's the possible alarms
    alarm_names = [*alarms.keys()]
    print("\nSelect alarms to create\n--------------------------")
    for count, alarm_name in enumerate(alarm_names):
        print(f"{count}: {alarm_name}")

    # stores choice of alarms and Validates the alarm choices
    validated = False
    while not validated:
        confirmation = input(
            "\nplease select alarm/alarms to create for the selected instances\n input comma-seperated list of correspoding indexes e.g '0,5,2' or 'a' for all instances\n - : "
        )
        validated = validate_list_entry(confirmation, alarm_names)

    # shrinks alarm variable down to only requested alarms
    if confirmation != "a":
        alarm_names = shrink_to_choices(confirmation, alarm_names)

    # confirms alarm choices
    confirmation = ""
    while confirmation not in ["Y", "y", "N", "n"]:
        print("\nConfirm alarm choice\n--------------------------")
        for alarm_name in alarm_names:
            print(alarm_name)
        confirmation = input("\nenter 'y' or 'n' to confirm/deny: ")
    if confirmation in ["N", "n"]:
        exit()
    client = boto3.client("cloudwatch")
    for instance in instances:
        for alarm_name in alarm_names:
            create_alarm(
                f"{prefix}-{instance['name']}-{alarm_name}",
                instance["id"],
                alarms[alarm_name],
                client,
            )


# TODO error handle csv reading
def alarms_from_csv(filepath, prefix) -> None:
    with open(filepath, mode="r") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        instance_alarms = []
        for row in csv_reader:
            instance_alarms.append(
                {
                    "name": row["name"],
                    "id": row["instance_id"],
                    "alarms": [alarm for alarm in row["alarms"].split(" ")],
                }
            )
    client = boto3.client("cloudwatch")
    for instance in instance_alarms:
        for alarm_name in instance["alarms"]:
            create_alarm(
                f"{prefix}-{instance['name']}-{alarm_name}",
                instance["id"],
                alarms[alarm_name],
                client,
            )


def main() -> None:
    logging.basicConfig(
        filename="create_base_alarms.log",
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    # setting up cmd line argument parse
    parser = argparse.ArgumentParser(
        description="This script is used to update the name of all cloudwatch alarms\
            that have a given prefix within a region to a lowecase value."
    )
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        "-i",
        action="store_true",
        help="allows you to toggle the interactive mode on",
    )
    group.add_argument(
        "-f",
        type=str,
        help="lets you provide to csv file to be used for creating the alarms",
    )

    args = parser.parse_args()
    prefix = "test"

    if args.i:
        run_interactive(prefix)
    else:
        alarms_from_csv(args.f, prefix)


if __name__ == "__main__":
    main()
