import json
from aws_cdk import core
from aws_cdk import aws_config as config
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_lambda_python as lambda_python
from aws_cdk import aws_iam as iam
from aws_cdk import aws_ssm as ssm


class AlbAutotagConfigRuleStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Contextual variables
        external_tag_key = self.node.try_get_context("external_tag_key")
        external_tag_value = self.node.try_get_context(
            "external_tag_value")
        internal_tag_key = self.node.try_get_context("internal_tag_key")
        internal_tag_value = self.node.try_get_context(
            "internal_tag_value")
        exception_tag_key = self.node.try_get_context(
            "exception_tag_key")
        exception_tag_value = self.node.try_get_context(
            "exception_tag_value")
        enforce_compliance = self.node.try_get_context("enforce_compliance")

        # Config Rule Lambda function
        lambda_function = lambda_python.PythonFunction(
            self, "ConfigRuleLambdaFunction",
            entry="./lambda",
            handler="lambda_handler",
            index="index.py",
            description="Config Rule to create tags on untagged ALB resources",
            timeout=core.Duration.seconds(10),
            tracing=lambda_.Tracing.ACTIVE,
            environment=dict(
                EXTERNAL_TAG_KEY=external_tag_key,
                EXTERNAL_TAG_VALUE=external_tag_value,
                INTERNAL_TAG_KEY=internal_tag_key,
                INTERNAL_TAG_VALUE=internal_tag_value,
                EXCEPTION_TAG_KEY=exception_tag_key,
                EXCEPTION_TAG_VALUE=exception_tag_value
            )
        )

        # Allow Lambda function to describe ELBs and read their tags
        lambda_function.add_to_role_policy(
            statement=iam.PolicyStatement(
                actions=[
                    "elasticloadbalancing:DescribeLoadBalancers",
                    "elasticloadbalancing:DescribeTags"
                ],
                effect=iam.Effect.ALLOW,
                resources=["*"],
                sid="AllowELBTagRead"
            )
        )

        # The Config Rule
        config_rule = config.CustomRule(
            self, "ConfigRule",
            lambda_function=lambda_function,
            configuration_changes=True,
            config_rule_name="alb-tag-enforcement",
            description="Checks if ALBs have the appropriate tag associated to them based on their ALB scheme"
        )

        # Scope the rule to only look at ELBv2
        config_rule.scope_to_resource(
            type="AWS::ElasticLoadBalancingV2::LoadBalancer")

        # For readability, define the SSM remediation document externally
        # and read it in here
        with open("./ssm/remediation_document.json", "r") as f:
            ssm_document = json.load(f)
        remediation_document = ssm.CfnDocument(
            self, "SSMRemediationDocument",
            document_type="Automation",
            content=ssm_document
        )

        # Give SSM permission to add the tag when remediation is needed
        remediation_role = iam.Role(
            self, "RemediationRole",
            assumed_by=iam.ServicePrincipal(
                service="ssm.amazonaws.com"
            ),
            description="Allow SSM to update tags on ALBs via a Config Rule remediation",
            inline_policies=dict(
                alb_read_write=iam.PolicyDocument(statements=[
                    iam.PolicyStatement(
                        actions=[
                            "elasticloadbalancing:DescribeLoadBalancers",
                            "elasticloadbalancing:DescribeTags",
                            "elasticloadbalancing:AddTags"
                        ],
                        effect=iam.Effect.ALLOW,
                        resources=["*"],
                        sid="AllowELBTagReadWrite"
                    )
                ])
            )
        )

        # If enforce compliance is true, automatically remediate non-compliant
        # resources. Otherwise, just report compliant and non-compliant
        # resources, but still allow for manual remediation.
        if enforce_compliance.lower() == "true":
            remediation_action = config.CfnRemediationConfiguration(
                self, "ConfigRemediationAction",
                automatic=True,
                config_rule_name=config_rule.config_rule_name,
                parameters=dict(
                    ALBArn=dict(ResourceValue=dict(Value="RESOURCE_ID")),
                    AutomationAssumeRole=dict(StaticValue=dict(
                        Values=[remediation_role.role_arn])),
                    ExternalTagKey=dict(StaticValue=dict(
                        Values=[external_tag_key])),
                    ExternalTagValue=dict(StaticValue=dict(
                        Values=[external_tag_value])),
                    InternalTagKey=dict(StaticValue=dict(
                        Values=[internal_tag_key])),
                    InternalTagValue=dict(StaticValue=dict(
                        Values=[internal_tag_value])),
                    ExceptionTagKey=dict(StaticValue=dict(
                        Values=[exception_tag_key])),
                    ExceptionTagValue=dict(StaticValue=dict(
                        Values=[exception_tag_value]))
                ),
                target_id=remediation_document.ref,
                target_type="SSM_DOCUMENT",
                maximum_automatic_attempts=3,
                retry_attempt_seconds=15
            )
        else:
            remediation_action = config.CfnRemediationConfiguration(
                self, "ConfigRemediationAction",
                automatic=False,
                config_rule_name=config_rule.config_rule_name,
                parameters=dict(
                    ALBArn=dict(ResourceValue=dict(Value="RESOURCE_ID")),
                    AutomationAssumeRole=dict(StaticValue=dict(
                        Values=[remediation_role.role_arn])),
                    ExternalTagKey=dict(StaticValue=dict(
                        Values=[external_tag_key])),
                    ExternalTagValue=dict(StaticValue=dict(
                        Values=[external_tag_value])),
                    InternalTagKey=dict(StaticValue=dict(
                        Values=[internal_tag_key])),
                    InternalTagValue=dict(StaticValue=dict(
                        Values=[internal_tag_value])),
                    ExceptionTagKey=dict(StaticValue=dict(
                        Values=[exception_tag_key])),
                    ExceptionTagValue=dict(StaticValue=dict(
                        Values=[exception_tag_value]))
                ),
                target_id=remediation_document.ref,
                target_type="SSM_DOCUMENT"
            )
