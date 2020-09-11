from aws_cdk import core
from aws_cdk import aws_config as config
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_lambda_python as lambda_python
from aws_cdk import aws_iam as iam


class AlbAutotagConfigRuleStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # The code that defines your stack goes here
        lambda_function = lambda_python.PythonFunction(
            self, "ConfigRuleLambdaFunction",
            entry="./assets",
            handler="lambda_handler",
            index="index.py",
            description="Config Rule to create tags on untagged ALB resources",
            timeout=core.Duration.seconds(10),
            tracing=lambda_.Tracing.ACTIVE,
            environment=dict(
                EXTERNAL_TAG_KEY=self.node.try_get_context("external_tag_key"),
                EXTERNAL_TAG_VALUE=self.node.try_get_context(
                    "external_tag_value"),
                INTERNAL_TAG_KEY=self.node.try_get_context("internal_tag_key"),
                INTERNAL_TAG_VALUE=self.node.try_get_context(
                    "internal_tag_value"),
                ENFORCE_COMPLIANCE=self.node.try_get_context(
                    "enforce_compliance")
            )
        )

        lambda_function.add_to_role_policy(
            statement=iam.PolicyStatement(
                actions=[
                    "elasticloadbalancing:DescribeLoadBalancers",
                    "elasticloadbalancing:DescribeTags",
                    "elasticloadbalancing:AddTags"
                ],
                effect=iam.Effect.ALLOW,
                resources=["*"],
                sid="AllowELBTagReadWrite"
            )
        )

        config_rule = config.CustomRule(
            self, "ConfigRule",
            lambda_function=lambda_function,
            configuration_changes=True,
            config_rule_name="alb-tag-enforcement",
            description="Checks if ALBs have the appropriate tag associated to them based on their ALB scheme"
        )

        config_rule.scope_to_resource(
            type="AWS::ElasticLoadBalancingV2::LoadBalancer")
