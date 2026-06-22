"""CloudTrail event collection with instance-level and security-group attribution."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from app.modules.aws.ai.finding_rules import SECURITY_EVENT_NAMES, analyze_security_groups
from app.modules.aws.client import AwsClientFactory
from app.modules.aws.models import (
    AwsCloudTrailEvent,
    AwsCloudTrailResult,
    AwsEc2Instance,
    AwsSecurityGroup,
)

TRACKED_EVENT_NAMES = [
    "RunInstances",
    "StartInstances",
    "StopInstances",
    "RebootInstances",
    "TerminateInstances",
    "ModifyInstanceAttribute",
    "AuthorizeSecurityGroupIngress",
    "AuthorizeSecurityGroupEgress",
    "RevokeSecurityGroupIngress",
    "RevokeSecurityGroupEgress",
    "ModifySecurityGroupRules",
    "CreateSecurityGroup",
    "DeleteSecurityGroup",
    "AttachVolume",
    "DetachVolume",
    "AssociateAddress",
    "DisassociateAddress",
    "CreateTags",
    "DeleteTags",
    "CreateAutoScalingGroup",
    "UpdateAutoScalingGroup",
    "TerminateInstanceInAutoScalingGroup",
    "SetDesiredCapacity",
]

TAG_EVENT_NAMES = {"CreateTags", "DeleteTags"}

STATE_CHANGE_EVENT_NAMES = {
    "StartInstances",
    "StopInstances",
    "RebootInstances",
    "TerminateInstances",
    "TerminateInstanceInAutoScalingGroup",
}

WINDOW_TO_HOURS = {"1h": 1, "24h": 24, "7d": 24 * 7}


class AwsCloudTrailCollector:
    def __init__(self, client_factory: AwsClientFactory | None = None) -> None:
        self.client_factory = client_factory or AwsClientFactory()

    async def collect(
        self,
        region: str,
        instances: list[AwsEc2Instance] | None = None,
        security_groups: list[AwsSecurityGroup] | None = None,
        lookback_hours: int | None = None,
        cloudwatch_window: str = "24h",
    ) -> AwsCloudTrailResult:
        hours = lookback_hours or WINDOW_TO_HOURS.get(cloudwatch_window, 24)
        return await asyncio.to_thread(
            self._collect_sync,
            region,
            instances or [],
            security_groups or [],
            hours,
        )

    def _collect_sync(
        self,
        region: str,
        instances: list[AwsEc2Instance],
        security_groups: list[AwsSecurityGroup],
        lookback_hours: int,
    ) -> AwsCloudTrailResult:
        cloudtrail = self.client_factory.client("cloudtrail", region)
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=lookback_hours)

        events_by_id: dict[str, AwsCloudTrailEvent] = {}
        try:
            target_instances = instances[:25]

            for event_name in TRACKED_EVENT_NAMES:
                self._lookup_by_event_name(
                    cloudtrail,
                    event_name,
                    start_time,
                    end_time,
                    events_by_id,
                )

            for instance in target_instances[:25]:
                self._lookup_by_resource_name(
                    cloudtrail,
                    instance.instance_id,
                    start_time,
                    end_time,
                    events_by_id,
                )

            target_group_ids = self._security_groups_for_lookup(security_groups)
            for group_id in target_group_ids[:30]:
                self._lookup_by_resource_name(
                    cloudtrail,
                    group_id,
                    start_time,
                    end_time,
                    events_by_id,
                )

            events = sorted(
                events_by_id.values(),
                key=lambda event: event.event_time or "",
                reverse=True,
            )

            instance_ids = {instance.instance_id for instance in target_instances[:25]}
            instance_events = self._dedupe_events(
                [event for event in events if self._event_targets_instances(event, instance_ids)]
            )[:100]

            security_group_events = self._dedupe_events(
                [
                    event
                    for event in events
                    if self._event_targets_security_groups(event, set(target_group_ids))
                ]
            )[:100]

            return AwsCloudTrailResult(
                collected=True,
                lookback_hours=lookback_hours,
                events=events[:250],
                instance_events=instance_events,
                security_group_events=security_group_events,
                tracked_event_names=TRACKED_EVENT_NAMES,
            )
        except Exception as exc:
            return AwsCloudTrailResult(
                collected=False,
                lookback_hours=lookback_hours,
                events=[],
                instance_events=[],
                security_group_events=[],
                tracked_event_names=TRACKED_EVENT_NAMES,
                error=str(exc),
            )

    def _security_groups_for_lookup(self, security_groups: list[AwsSecurityGroup]) -> list[str]:
        internet_exposed, _ = analyze_security_groups(
            [group.model_dump() for group in security_groups]
        )
        priority_ids = {str(rule.get("security_group_id")) for rule in internet_exposed}
        all_ids = [group.security_group_id for group in security_groups if group.security_group_id]
        ordered = [group_id for group_id in all_ids if group_id in priority_ids]
        ordered.extend(group_id for group_id in all_ids if group_id not in priority_ids)
        return ordered

    def _lookup_by_event_name(
        self,
        cloudtrail: Any,
        event_name: str,
        start_time: datetime,
        end_time: datetime,
        events_by_id: dict[str, AwsCloudTrailEvent],
    ) -> None:
        next_token: str | None = None
        pages = 0
        while pages < 3:
            params: dict[str, Any] = {
                "LookupAttributes": [
                    {"AttributeKey": "EventName", "AttributeValue": event_name}
                ],
                "StartTime": start_time,
                "EndTime": end_time,
                "MaxResults": 50,
            }
            if next_token:
                params["NextToken"] = next_token
            response = cloudtrail.lookup_events(**params)
            for item in response.get("Events", []):
                parsed = self._parse_event_item(item, event_name)
                if parsed.event_id:
                    events_by_id[parsed.event_id] = parsed
            next_token = response.get("NextToken")
            pages += 1
            if not next_token:
                break

    def _lookup_by_resource_name(
        self,
        cloudtrail: Any,
        resource_name: str,
        start_time: datetime,
        end_time: datetime,
        events_by_id: dict[str, AwsCloudTrailEvent],
    ) -> None:
        response = cloudtrail.lookup_events(
            LookupAttributes=[{"AttributeKey": "ResourceName", "AttributeValue": resource_name}],
            StartTime=start_time,
            EndTime=end_time,
            MaxResults=50,
        )
        for item in response.get("Events", []):
            parsed = self._parse_event_item(item, item.get("EventName"))
            if resource_name.startswith("sg-"):
                group_ids = list(parsed.security_group_ids)
                if resource_name not in group_ids:
                    group_ids.append(resource_name)
                parsed = parsed.model_copy(update={"security_group_ids": group_ids})
            elif resource_name not in parsed.instance_ids:
                parsed = parsed.model_copy(
                    update={"instance_ids": [*parsed.instance_ids, resource_name]}
                )
            if parsed.event_id:
                events_by_id[parsed.event_id] = parsed

    def _parse_event_item(self, item: dict[str, Any], event_name: str | None) -> AwsCloudTrailEvent:
        cloud_trail_event = item.get("CloudTrailEvent")
        payload: dict[str, Any] = {}
        if cloud_trail_event:
            try:
                payload = json.loads(cloud_trail_event)
            except json.JSONDecodeError:
                payload = {}

        user_identity = payload.get("userIdentity") or {}
        session_context = user_identity.get("sessionContext") or {}
        session_issuer = session_context.get("sessionIssuer") or {}
        request_parameters = payload.get("requestParameters") or {}

        instance_ids = self._extract_instance_ids(request_parameters, item.get("Resources") or [])
        security_group_ids, rule_summary = self._extract_security_group_context(
            request_parameters,
            item.get("Resources") or [],
            item.get("EventName") or event_name,
        )
        tag_summary = self._extract_tag_summary(
            request_parameters,
            item.get("EventName") or event_name,
        )
        principal_arn = user_identity.get("arn")
        principal_type = user_identity.get("type")
        username = item.get("Username") or user_identity.get("userName") or principal_arn

        if principal_type == "AssumedRole" and session_issuer.get("userName"):
            username = (
                f"{session_issuer.get('userName')} "
                f"(role: {session_issuer.get('arn') or principal_arn})"
            )

        resources = item.get("Resources") or []
        resource = resources[0] if resources else {}

        return AwsCloudTrailEvent(
            event_id=item.get("EventId"),
            event_name=item.get("EventName") or event_name,
            event_time=item.get("EventTime").isoformat()
            if item.get("EventTime") is not None
            else None,
            username=username,
            principal_arn=principal_arn,
            principal_type=principal_type,
            resource_type=resource.get("ResourceType"),
            resource_name=resource.get("ResourceName"),
            instance_ids=instance_ids,
            security_group_ids=security_group_ids,
            rule_summary=rule_summary,
            tag_summary=tag_summary,
            source_ip=payload.get("sourceIPAddress"),
            user_agent=payload.get("userAgent"),
            read_only=item.get("ReadOnly") == "true",
            error_code=item.get("ErrorCode"),
            event_source=payload.get("eventSource"),
        )

    def _extract_instance_ids(
        self,
        request_parameters: dict[str, Any],
        resources: list[dict[str, Any]],
    ) -> list[str]:
        instance_ids: list[str] = []

        raw_ids = request_parameters.get("instancesSet", {}).get("items") or request_parameters.get(
            "instanceIds"
        )
        if isinstance(raw_ids, list):
            for entry in raw_ids:
                if isinstance(entry, dict) and entry.get("instanceId"):
                    instance_ids.append(entry["instanceId"])
                elif isinstance(entry, str):
                    instance_ids.append(entry)
        elif isinstance(raw_ids, str):
            instance_ids.append(raw_ids)

        for resource in resources:
            resource_name = resource.get("ResourceName")
            if resource_name and resource_name.startswith("i-"):
                instance_ids.append(resource_name)

        for entry in (request_parameters.get("resourcesSet") or {}).get("items") or []:
            if isinstance(entry, dict):
                resource_id = entry.get("resourceId")
                if resource_id and str(resource_id).startswith("i-"):
                    instance_ids.append(str(resource_id))

        return sorted(set(instance_ids))

    def _extract_tag_summary(
        self,
        request_parameters: dict[str, Any],
        event_name: str | None,
    ) -> str | None:
        if event_name not in TAG_EVENT_NAMES:
            return None

        tag_items = (request_parameters.get("tagSet") or {}).get("items") or []
        summaries: list[str] = []
        for item in tag_items:
            if not isinstance(item, dict):
                continue
            key = item.get("key")
            if not key:
                continue
            if event_name == "DeleteTags":
                summaries.append(str(key))
            else:
                value = item.get("value")
                summaries.append(f"{key}={value}" if value is not None else str(key))

        return ", ".join(summaries) if summaries else None

    def _extract_security_group_context(
        self,
        request_parameters: dict[str, Any],
        resources: list[dict[str, Any]],
        event_name: str | None,
    ) -> tuple[list[str], str | None]:
        group_ids: set[str] = set()
        summaries: list[str] = []

        group_id = request_parameters.get("groupId")
        if isinstance(group_id, str) and group_id.startswith("sg-"):
            group_ids.add(group_id)

        for resource in resources:
            resource_name = resource.get("ResourceName")
            if resource_name and str(resource_name).startswith("sg-"):
                group_ids.add(str(resource_name))

        if event_name in {"AuthorizeSecurityGroupIngress", "AuthorizeSecurityGroupEgress"}:
            for item in (request_parameters.get("ipPermissions") or {}).get("items", []):
                summaries.append(self._summarize_ip_permission(item))
        elif event_name == "ModifySecurityGroupRules":
            for item in (request_parameters.get("securityGroupRules") or {}).get("items", []):
                item_group = item.get("groupId")
                if item_group:
                    group_ids.add(str(item_group))
                summaries.append(self._summarize_modify_rule(item))

        rule_summary = "; ".join(summary for summary in summaries if summary) or None
        return sorted(group_ids), rule_summary

    def _summarize_ip_permission(self, item: dict[str, Any]) -> str:
        protocol = item.get("ipProtocol") or "?"
        from_port = item.get("fromPort")
        to_port = item.get("toPort")
        port = from_port if from_port == to_port else f"{from_port}-{to_port}"
        cidrs = [
            entry.get("cidrIp")
            for entry in (item.get("ipRanges") or {}).get("items", [])
            if entry.get("cidrIp")
        ]
        ipv6 = [
            entry.get("cidrIpv6")
            for entry in (item.get("ipv6Ranges") or {}).get("items", [])
            if entry.get("cidrIpv6")
        ]
        sources = ", ".join(cidrs + ipv6) or "unknown"
        return f"{protocol} {port} from {sources}"

    def _summarize_modify_rule(self, item: dict[str, Any]) -> str:
        protocol = item.get("ipProtocol") or "?"
        from_port = item.get("fromPort")
        to_port = item.get("toPort")
        port = from_port if from_port == to_port else f"{from_port}-{to_port}"
        cidr = item.get("cidrIpv4") or item.get("cidrIpv6") or "unknown"
        direction = "egress" if item.get("isEgress") else "ingress"
        return f"{direction} {protocol} {port} from {cidr}"

    def _dedupe_events(self, events: list[AwsCloudTrailEvent]) -> list[AwsCloudTrailEvent]:
        seen: set[str] = set()
        unique: list[AwsCloudTrailEvent] = []
        for event in events:
            key = event.event_id or f"{event.event_name}:{event.event_time}:{event.username}"
            if key in seen:
                continue
            seen.add(key)
            unique.append(event)
        return unique

    def _event_targets_instances(
        self,
        event: AwsCloudTrailEvent,
        instance_ids: set[str],
    ) -> bool:
        if event.event_name in TAG_EVENT_NAMES and event.instance_ids:
            if instance_ids.intersection(event.instance_ids):
                return True
        if event.instance_ids and instance_ids.intersection(event.instance_ids):
            return True
        if event.resource_name and event.resource_name in instance_ids:
            return True
        return False

    def _event_targets_security_groups(
        self,
        event: AwsCloudTrailEvent,
        group_ids: set[str],
    ) -> bool:
        if event.event_name not in SECURITY_EVENT_NAMES:
            return False
        if event.security_group_ids and group_ids.intersection(event.security_group_ids):
            return True
        if event.resource_name and event.resource_name in group_ids:
            return True
        return False
