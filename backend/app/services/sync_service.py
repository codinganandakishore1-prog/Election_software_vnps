"""Vote synchronization service."""

from __future__ import annotations

from datetime import datetime, timezone

from election_platform.enums.admin import SyncLogStatus
from election_platform.enums.election import ElectionStatus, ElectionType
from election_platform.enums.sync import QueueStatus
from election_platform.logging.setup import get_logger

from app.database.base import utc_now
from app.database.seeds import new_uuid
from app.exceptions.base import ForbiddenError, NotFoundError, ValidationError
from app.models.audit_log import AuditLog
from app.models.sync import SyncLog, Vote, VoteQueue
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.election_repository import ElectionRepository
from app.repositories.node_repository import NodeRepository, SyncLogRepository, VoteQueueRepository
from app.repositories.position_repository import PositionRepository
from app.repositories.vote_repository import VoteRepository
from app.schemas.sync import SyncResponse, SyncVersionResponse, VotePayload, VoteUploadRequest
from app.services.base import BaseService

logger = get_logger("synchronization")


class SyncService(BaseService):
    """Handles vote upload, validation, deduplication, and queue processing."""

    def __init__(
        self,
        vote_repository: VoteRepository,
        node_repository: NodeRepository,
        election_repository: ElectionRepository,
        position_repository: PositionRepository,
        candidate_repository: CandidateRepository,
        vote_queue_repository: VoteQueueRepository,
        sync_log_repository: SyncLogRepository,
        audit_log_repository: AuditLogRepository,
    ) -> None:
        self.vote_repository = vote_repository
        self.node_repository = node_repository
        self.election_repository = election_repository
        self.position_repository = position_repository
        self.candidate_repository = candidate_repository
        self.vote_queue_repository = vote_queue_repository
        self.sync_log_repository = sync_log_repository
        self.audit_log_repository = audit_log_repository

    def get_sync_version(self, node_id: str) -> SyncVersionResponse:
        """Return the configuration version expected for the authenticated node."""
        node = self._get_node_or_raise(node_id)
        return SyncVersionResponse(
            latest_version=node.config_version,
            download_required=False,
        )

    def upload_votes(
        self,
        payload: VoteUploadRequest,
        authenticated_node_id: str,
        *,
        ip_address: str | None = None,
    ) -> SyncResponse:
        """Validate and persist a vote batch from a voting node."""
        if payload.node_id != authenticated_node_id:
            raise ForbiddenError("Token does not match node")

        node = self._get_node_or_raise(authenticated_node_id)
        if payload.config_version != node.config_version:
            raise ValidationError(
                f"Configuration version mismatch: node has {node.config_version}, "
                f"received {payload.config_version}"
            )

        sync_start = utc_now()
        accepted: list[str] = []
        duplicates: list[str] = []
        failed: list[str] = []

        for vote_payload in payload.votes:
            result = self._process_vote(vote_payload, node_id=authenticated_node_id)
            if result == "accepted":
                accepted.append(vote_payload.vote_uuid)
            elif result == "duplicate":
                duplicates.append(vote_payload.vote_uuid)
            else:
                failed.append(vote_payload.vote_uuid)

        self._write_sync_log(
            node_id=authenticated_node_id,
            sync_start=sync_start,
            total=len(payload.votes),
            accepted=len(accepted),
            failed=len(failed),
        )
        self._audit_sync(
            node_id=authenticated_node_id,
            accepted=accepted,
            duplicates=duplicates,
            failed=failed,
            ip_address=ip_address,
        )
        self.vote_repository.commit()

        logger.info(
            "Sync batch for node %s: %s accepted, %s duplicates, %s failed",
            authenticated_node_id,
            len(accepted),
            len(duplicates),
            len(failed),
        )
        return SyncResponse(
            success=len(failed) == 0,
            accepted=accepted,
            duplicates=duplicates,
            failed=failed,
        )

    def _process_vote(self, payload: VotePayload, *, node_id: str) -> str:
        """Process a single vote. Returns 'accepted', 'duplicate', or 'failed'."""
        if self.vote_repository.exists_by_vote_uuid(payload.vote_uuid):
            logger.debug("Duplicate vote %s ignored", payload.vote_uuid)
            return "duplicate"

        if not self._validate_vote(payload, node_id=node_id):
            self._record_failed_queue(payload, node_id=node_id)
            return "failed"

        voted_at = self._parse_timestamp(payload.timestamp)
        election_type = self._parse_election_type(payload.election_type)
        now = utc_now()

        self.vote_repository.add(
            Vote(
                vote_uuid=payload.vote_uuid,
                election_id=payload.election_id,
                position_id=payload.position_id,
                candidate_id=payload.candidate_id,
                node_id=node_id,
                election_type=election_type,
                house_id=payload.house_id,
                voted_at=voted_at,
                synced_at=now,
            )
        )
        self.vote_queue_repository.add(
            VoteQueue(
                vote_uuid=payload.vote_uuid,
                node_id=node_id,
                received_time=now,
                processed_time=now,
                retry_count=0,
                queue_status=QueueStatus.COMPLETED,
            )
        )
        return "accepted"

    def _validate_vote(self, payload: VotePayload, *, node_id: str) -> bool:
        election = self.election_repository.get_by_id(payload.election_id)
        if election is None or election.deleted_at is not None:
            logger.warning("Vote %s rejected: election %s not found", payload.vote_uuid, payload.election_id)
            return False
        if election.status != ElectionStatus.LIVE:
            logger.warning(
                "Vote %s rejected: election %s is %s (must be Live)",
                payload.vote_uuid,
                payload.election_id,
                getattr(election.status, "value", election.status),
            )
            return False

        position = self.position_repository.get_by_id(payload.position_id)
        if position is None or position.deleted_at is not None:
            logger.warning("Vote %s rejected: position %s not found", payload.vote_uuid, payload.position_id)
            return False
        if position.election_id != payload.election_id:
            logger.warning("Vote %s rejected: position does not belong to election", payload.vote_uuid)
            return False

        candidate = self.candidate_repository.get_by_id(payload.candidate_id)
        if candidate is None or candidate.deleted_at is not None:
            logger.warning("Vote %s rejected: candidate %s not found", payload.vote_uuid, payload.candidate_id)
            return False
        if candidate.position_id != payload.position_id:
            logger.warning("Vote %s rejected: candidate does not belong to position", payload.vote_uuid)
            return False
        if candidate.election_id != payload.election_id:
            logger.warning("Vote %s rejected: candidate does not belong to election", payload.vote_uuid)
            return False

        node = self.node_repository.get_by_id(node_id)
        if node is None:
            return False

        try:
            election_type = ElectionType(payload.election_type)
        except ValueError:
            logger.warning("Vote %s rejected: invalid election type %s", payload.vote_uuid, payload.election_type)
            return False

        if node.election_type != election_type:
            logger.warning("Vote %s rejected: election type mismatch with node", payload.vote_uuid)
            return False

        return True

    def _record_failed_queue(self, payload: VotePayload, *, node_id: str) -> None:
        existing = self.vote_queue_repository.get_by_vote_uuid(payload.vote_uuid)
        if existing is not None:
            existing.retry_count += 1
            existing.queue_status = QueueStatus.FAILED
            return

        self.vote_queue_repository.add(
            VoteQueue(
                vote_uuid=payload.vote_uuid,
                node_id=node_id,
                received_time=utc_now(),
                processed_time=None,
                retry_count=1,
                queue_status=QueueStatus.FAILED,
            )
        )

    def _write_sync_log(
        self,
        *,
        node_id: str,
        sync_start: datetime,
        total: int,
        accepted: int,
        failed: int,
    ) -> None:
        if total == 0:
            return

        if failed == 0:
            status = SyncLogStatus.SUCCESS
        elif accepted > 0:
            status = SyncLogStatus.PARTIAL
        else:
            status = SyncLogStatus.FAILED

        self.sync_log_repository.add(
            SyncLog(
                node_id=node_id,
                sync_start=sync_start,
                sync_end=utc_now(),
                total_votes=total,
                successful_votes=accepted,
                failed_votes=failed,
                status=status,
            )
        )

    def _audit_sync(
        self,
        *,
        node_id: str,
        accepted: list[str],
        duplicates: list[str],
        failed: list[str],
        ip_address: str | None,
    ) -> None:
        if not accepted and not duplicates and not failed:
            return

        self.audit_log_repository.add(
            AuditLog(
                id=new_uuid(),
                user_id=None,
                module="Synchronization",
                action="Vote Upload",
                new_value={
                    "node_id": node_id,
                    "accepted": len(accepted),
                    "duplicates": len(duplicates),
                    "failed": len(failed),
                },
                ip_address=ip_address,
            )
        )

    def _get_node_or_raise(self, node_id: str):
        node = self.node_repository.get_by_id(node_id)
        if node is None or not node.active:
            raise NotFoundError("Voting node not found")
        return node

    @staticmethod
    def _parse_timestamp(timestamp: str) -> datetime:
        try:
            parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValidationError(f"Invalid vote timestamp: {timestamp}") from exc
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed

    @staticmethod
    def _parse_election_type(value: str) -> ElectionType:
        try:
            return ElectionType(value)
        except ValueError as exc:
            raise ValidationError(f"Invalid election type: {value}") from exc
