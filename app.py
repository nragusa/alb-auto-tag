#!/usr/bin/env python3

from aws_cdk import core

from alb_autotag_config_rule.alb_autotag_config_rule_stack import AlbAutotagConfigRuleStack


app = core.App()
AlbAutotagConfigRuleStack(app, "alb-autotag-config-rule")

app.synth()
