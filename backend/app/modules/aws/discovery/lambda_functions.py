"""AWS Lambda function discovery."""

from __future__ import annotations

import asyncio
from typing import Any

from app.modules.aws.client import AwsClientFactory
from app.modules.aws.models import AwsLambdaEventSource, AwsLambdaFunction
from app.modules.aws.utils import parse_tags


class AwsLambdaDiscovery:
    def __init__(self, client_factory: AwsClientFactory | None = None) -> None:
        self.client_factory = client_factory or AwsClientFactory()

    async def discover(self, region: str) -> list[AwsLambdaFunction]:
        return await asyncio.to_thread(self._discover_sync, region)

    def _discover_sync(self, region: str) -> list[AwsLambdaFunction]:
        client = self.client_factory.client("lambda", region)
        functions: list[AwsLambdaFunction] = []

        paginator = client.get_paginator("list_functions")
        for page in paginator.paginate():
            for item in page.get("Functions", []):
                function_name = item.get("FunctionName", "")
                if not function_name:
                    continue
                functions.append(self._enrich_function(client, item))

        return functions

    def _enrich_function(self, client: Any, summary: dict[str, Any]) -> AwsLambdaFunction:
        function_name = summary.get("FunctionName", "")
        function_arn = summary.get("FunctionArn", "")

        config = summary
        try:
            response = client.get_function_configuration(FunctionName=function_name)
            config = response
        except Exception:
            pass

        vpc_config = config.get("VpcConfig") or {}
        environment = config.get("Environment") or {}
        environment_keys = sorted((environment.get("Variables") or {}).keys())

        event_sources = self._event_sources(client, function_name)
        tags = self._tags(client, function_arn)

        return AwsLambdaFunction(
            function_name=function_name,
            function_arn=function_arn,
            runtime=config.get("Runtime"),
            handler=config.get("Handler"),
            memory_size=config.get("MemorySize"),
            timeout=config.get("Timeout"),
            state=config.get("State"),
            state_reason=config.get("StateReason"),
            last_update_status=config.get("LastUpdateStatus"),
            role=config.get("Role"),
            vpc_id=vpc_config.get("VpcId") or None,
            subnet_ids=[subnet for subnet in vpc_config.get("SubnetIds", []) if subnet],
            security_group_ids=[
                group_id for group_id in vpc_config.get("SecurityGroupIds", []) if group_id
            ],
            environment_keys=environment_keys,
            event_sources=event_sources,
            tags=tags,
            description=config.get("Description"),
        )

    def _event_sources(self, client: Any, function_name: str) -> list[AwsLambdaEventSource]:
        mappings: list[AwsLambdaEventSource] = []
        try:
            paginator = client.get_paginator("list_event_source_mappings")
            for page in paginator.paginate(FunctionName=function_name):
                for item in page.get("EventSourceMappings", []):
                    source_arn = item.get("EventSourceArn")
                    mappings.append(
                        AwsLambdaEventSource(
                            uuid=item.get("UUID", ""),
                            event_source_arn=source_arn,
                            event_source_type=self._event_source_type(source_arn),
                            state=item.get("State"),
                            batch_size=item.get("BatchSize"),
                        )
                    )
        except Exception:
            return mappings
        return mappings

    def _tags(self, client: Any, function_arn: str) -> dict[str, str]:
        if not function_arn:
            return {}
        try:
            response = client.list_tags(Resource=function_arn)
            return parse_tags(
                [{"Key": key, "Value": value} for key, value in (response.get("Tags") or {}).items()]
            )
        except Exception:
            return {}

    def _event_source_type(self, event_source_arn: str | None) -> str | None:
        if not event_source_arn:
            return None
        if ":sqs:" in event_source_arn:
            return "sqs"
        if ":dynamodb:" in event_source_arn:
            return "dynamodb"
        if ":kinesis:" in event_source_arn:
            return "kinesis"
        if ":kafka:" in event_source_arn:
            return "kafka"
        if ":mq:" in event_source_arn:
            return "mq"
        return "other"
