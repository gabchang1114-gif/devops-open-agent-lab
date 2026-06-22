"""GitHub REST API client for PR review operations."""

from __future__ import annotations

from typing import Any

import httpx
from loguru import logger

from app.core.config import Settings, get_settings
from app.core.errors import sanitize_error_message
from app.modules.pr_reviewer.github.file_classifier import classify_file
from app.modules.pr_reviewer.models.schemas import PrFileInfo, PrWebhookPayload


class GitHubClientError(Exception):
    """Raised when GitHub API calls fail."""


class GitHubClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.base_url = self.settings.github_api_base_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        token = self.settings.github_token.strip()
        if not token:
            raise GitHubClientError("GitHub token is not configured")
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def fetch_pull_request(
        self,
        owner: str,
        repo: str,
        pull_number: int,
    ) -> dict[str, Any]:
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pull_number}"
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url, headers=self._headers())
        if response.status_code == 404:
            raise GitHubClientError("Pull request not found")
        if response.status_code == 401:
            raise GitHubClientError(
                "GitHub authentication failed. Verify GITHUB_TOKEN has access to this repository."
            )
        if response.status_code == 403 and "rate limit" in response.text.lower():
            raise GitHubClientError("GitHub API rate limit exceeded")
        if response.status_code >= 400:
            raise GitHubClientError(
                sanitize_error_message(f"GitHub API error ({response.status_code})")
            )
        return response.json()

    async def fetch_pull_request_files(
        self,
        owner: str,
        repo: str,
        pull_number: int,
    ) -> list[PrFileInfo]:
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pull_number}/files"
        files: list[PrFileInfo] = []
        page = 1
        async with httpx.AsyncClient(timeout=60.0) as client:
            while True:
                response = await client.get(
                    url,
                    headers=self._headers(),
                    params={"per_page": 100, "page": page},
                )
                if response.status_code == 404:
                    raise GitHubClientError("Repository or pull request not found")
                if response.status_code == 401:
                    raise GitHubClientError(
                        "GitHub authentication failed. Verify GITHUB_TOKEN has access to this repository."
                    )
                if response.status_code == 403 and "rate limit" in response.text.lower():
                    raise GitHubClientError("GitHub API rate limit exceeded")
                if response.status_code >= 400:
                    raise GitHubClientError(
                        sanitize_error_message(
                            f"GitHub API error fetching PR files ({response.status_code})"
                        )
                    )
                batch = response.json()
                if not batch:
                    break
                for item in batch:
                    files.append(self._parse_file_item(item))
                if len(batch) < 100:
                    break
                page += 1
        return files

    def _parse_file_item(self, item: dict[str, Any]) -> PrFileInfo:
        filename = item.get("filename", "")
        patch = item.get("patch")
        skipped = False
        skip_reason: str | None = None
        if item.get("binary"):
            skipped = True
            skip_reason = "binary file"
        elif patch is None:
            skipped = True
            skip_reason = "no patch available"
        elif len(patch) > 12000:
            skipped = True
            skip_reason = "patch too large"
        return PrFileInfo(
            filename=filename,
            status=item.get("status", "modified"),
            additions=int(item.get("additions", 0)),
            deletions=int(item.get("deletions", 0)),
            changes=int(item.get("changes", 0)),
            patch=patch if not skipped else None,
            raw_url=item.get("raw_url"),
            blob_url=item.get("blob_url"),
            category=classify_file(filename),
            skipped=skipped,
            skip_reason=skip_reason,
        )

    async def post_issue_comment(
        self,
        owner: str,
        repo: str,
        pull_number: int,
        body: str,
    ) -> str:
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{pull_number}/comments"
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=self._headers(), json={"body": body})
        if response.status_code == 401:
            raise GitHubClientError(
                "GitHub authentication failed. Verify GITHUB_TOKEN can post comments on this repository."
            )
        if response.status_code >= 400:
            logger.error(
                "Failed to post GitHub PR comment | status={} repo={}/{} pr={}",
                response.status_code,
                owner,
                repo,
                pull_number,
            )
            raise GitHubClientError(
                sanitize_error_message(
                    f"Failed to post GitHub comment ({response.status_code})"
                )
            )
        payload = response.json()
        return str(payload.get("html_url", ""))

    @staticmethod
    def parse_webhook_payload(payload: dict[str, Any]) -> PrWebhookPayload | None:
        action = payload.get("action", "")
        if action not in {"opened", "synchronize", "reopened"}:
            return None
        pull_request = payload.get("pull_request") or {}
        repository = payload.get("repository") or {}
        owner_info = repository.get("owner") or {}
        owner = owner_info.get("login", "")
        repo = repository.get("name", "")
        if not owner or not repo:
            return None
        user = pull_request.get("user") or {}
        return PrWebhookPayload(
            owner=owner,
            repository=repo,
            pull_request_number=int(pull_request.get("number", 0)),
            pull_request_title=pull_request.get("title", ""),
            pull_request_body=pull_request.get("body") or "",
            pull_request_author=user.get("login", ""),
            base_branch=(pull_request.get("base") or {}).get("ref", ""),
            head_branch=(pull_request.get("head") or {}).get("ref", ""),
            commit_sha=(pull_request.get("head") or {}).get("sha", ""),
            action=action,
            changed_files_url=pull_request.get("url"),
        )
