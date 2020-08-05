# timeular-to-slack

Changes Slack status based on Timeular Status

First off, credit to [timeularslack](https://github.com/mapledyne/timeularslack)

This is an AWS Lambda function for changing your Slack status and DND settings based 
on your current Timeular activity.

## Installation

Create a Lambda function with the following settings

| Setting | Value |
| --- | --- |
| runtime | Python 3.8 |
| IAM role | generic one with basic permissions |
| memory | 128MB |
| timeout | 3 seconds |

Configure the following environment variables

| Name     | Description | Default |
| --- | --- | --- |
| DEBUG_LEVEL | logging level (DEBUG, INFO, WARN, etc. | WARN |
| DEBUG_BOTO_LEVEL | logging level for boto library | CRITICAL |
| SLACK_API_TOKEN | Slack App User API Token | |
| SLACK_SNOOZE_DURATION | duration in minutes of snooze in slack when configured | 60 |
| TIMEULAR_API_KEY | Timeular API key | |
| TIMEULAR_API_SECRET | Timeular API secret | |

## Configuration

Configuring the Slack status for each Timeular activity is handled in the code
by the dictionary named `TIMEULAR_ACTIVITY_TO_SLACK_STATUS`. The format of the 
dictionary goes as follows:

```python
TIMEULAR_ACTIVITY_TO_SLACK_STATUS = {
    'Working': {
        'text': 'Focused Work',
        'emoji': ':thinking_face:',
        'snooze': True
    },
    'Meeting': {
        'text': 'In a meeting',
        'emoji': ':calendar:',
        'snooze': True
    }
}
```

* **Working** and **Meeting** are the exact wording of the Timeular activity.
* **text** will be the Slack status text that will be set. Can be `''` for an empty status.
* **emoji** will be the Slack status emoji that will be set. Can be `''` if you want no emoji.
* **snooze** if _True_ then notifications will be snoozed for `SLACK_SNOOZE_DURATION` minutes

If there is no matching Timeular activity or not current activity at all, then the Slack status 
will be set to an empty text and emoji. Snooze will also be disabled.