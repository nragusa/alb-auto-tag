# ALB Tag Config Rule

To get up and running, first make sure you have the [CDK installed](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html#getting_started_install).

Once installed, create a python virtual environment, and install the required depencies:

```
virtualenv .env
source .env/bin/activate
pip install -r requirements.txt
```

Now you should edit the `cdk.json` file for your environment. The following variables should be set accordingly:

```
    "external_tag_key": "ExternalALB",
    "external_tag_value": "true",
    "internal_tag_key": "InternalALB",
    "internal_tag_value": "true",
    "exception_tag_key": "WAFException",
    "exception_tag_value": "false",
    "enforce_compliance": "true"
```

_Note_: You may want to set `enforce_compliance` to `false` to start. When the rule is run with this set to `false`, it will report **COMPLIANT** and **NON-COMPLIANT** resources in the AWS Config interface. If you'd like to have the rule automatically set the tags, set this to `true`.

You can now deploy the stack:

```
cdk deploy
```

## Useful commands

- `cdk ls` list all stacks in the app
- `cdk synth` emits the synthesized CloudFormation template
- `cdk deploy` deploy this stack to your default AWS account/region
- `cdk diff` compare deployed stack with current state
- `cdk docs` open CDK documentation
