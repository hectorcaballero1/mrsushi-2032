import os
import json
import boto3

events = boto3.client("events")
EVENT_BUS = os.environ["EVENT_BUS"]


def put_event(source, detail_type, detail):
    entries = [
        {
            "Source": source,
            "DetailType": detail_type,
            "Detail": json.dumps(detail, default=str),
            "EventBusName": EVENT_BUS,
        }
    ]
    events.put_events(Entries=entries)
