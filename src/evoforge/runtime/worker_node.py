import os
import time

import httpx
import structlog

from evoforge.memory.state import WorkflowState
from evoforge.orchestrator.engine import OrchestratorEngine
from evoforge.orchestrator.workflows import WorkflowDefinition, WorkflowTask

logger = structlog.get_logger(__name__)

class BaseWorkerNode:
    def __init__(self, control_plane_url: str, worker_id: str, token: str, worker_type: str, poll_interval: int = 15):
        self.control_plane_url = control_plane_url.rstrip("/")
        self.worker_id = worker_id
        self.token = token
        self.worker_type = worker_type
        self.poll_interval = poll_interval
        self._running = False
        self.client = httpx.Client(
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=10.0
        )
        self.current_workflow_id = None
        self.current_task_id = None
        
        # Will be set by subclasses
        self.capabilities = []
        self.compute_mode = "HYBRID"
        self.orchestrator = None

    def register(self):
        logger.info("worker_registering", worker_id=self.worker_id, type=self.worker_type)
        payload = {
            "worker_id": self.worker_id,
            "worker_type": self.worker_type,
            "status": "IDLE",
            "capabilities": self.capabilities,
            "compute_mode": self.compute_mode,
            "hostname": os.uname().nodename if hasattr(os, "uname") else "unknown",
            "version": "1.0.0",
            "health": "HEALTHY"
        }
        
        try:
            resp = self.client.post(f"{self.control_plane_url}/api/workers/register", json=payload)
            resp.raise_for_status()
            logger.info("worker_registered")
        except Exception as e:
            logger.error("worker_registration_failed", error=str(e))
            raise

    def heartbeat(self, status: str = "IDLE", health: str = "HEALTHY"):
        payload = {
            "status": status,
            "health": health,
            "current_workflow_id": self.current_workflow_id,
            "current_task_id": self.current_task_id
        }
        try:
            resp = self.client.post(f"{self.control_plane_url}/api/workers/{self.worker_id}/heartbeat", json=payload)
            resp.raise_for_status()
        except Exception as e:
            logger.warning("worker_heartbeat_failed", error=str(e))

    def check_for_work(self) -> dict | None:
        """Poll the control plane for a workflow to execute."""
        try:
            resp = self.client.post(f"{self.control_plane_url}/api/workers/{self.worker_id}/request-work")
            if resp.status_code == 200:
                data = resp.json()
                if "workflow" in data:
                    return data["workflow"]
        except Exception as e:
            logger.warning("worker_request_work_failed", error=str(e))
        return None

    def _build_workflow_definition(self, workflow_data: dict) -> WorkflowDefinition:
        tasks = []
        for t in workflow_data.get("tasks", []):
            from evoforge.orchestrator.workflows import TaskPriority
            tasks.append(WorkflowTask(
                id=t["id"],
                name=t.get("name", "Unnamed Task"),
                description=t["description"],
                priority=TaskPriority.MEDIUM,
                agent_type=t.get("agent_type", "developer")
            ))
        return WorkflowDefinition(
            id=workflow_data["id"],
            repo_name=workflow_data["repo_name"],
            tasks=tasks,
            dry_run=workflow_data.get("dry_run", False)
        )

    def execute_work(self, workflow_data: dict):
        if not self.orchestrator:
            logger.error("worker_has_no_orchestrator")
            return
            
        self.current_workflow_id = workflow_data["id"]
        self.heartbeat(status="BUSY")
        
        wdef = self._build_workflow_definition(workflow_data)
        state_json = workflow_data.get("state_snapshot")
        state = None
        if state_json:
            state = WorkflowState.model_validate_json(state_json)
        
        logger.info("worker_executing_workflow", workflow_id=self.current_workflow_id)
        
        # Override orchestrator worker id so lease logic uses this worker's ID
        self.orchestrator.worker_id = self.worker_id
        
        try:
            self.orchestrator.execute_workflow(wdef, state=state)
        except Exception as e:
            logger.exception("worker_execution_crashed", error=str(e))
        finally:
            self.current_workflow_id = None
            self.current_task_id = None
            # Release lease via API
            try:
                self.client.post(f"{self.control_plane_url}/api/workers/{self.worker_id}/release-work", json={"workflow_id": workflow_data["id"]})
            except Exception as e:
                logger.warning("failed_to_release_lease_via_api", error=str(e))
            self.heartbeat(status="IDLE")

    def run(self):
        self.register()
        self._running = True
        logger.info("worker_started_polling", interval=self.poll_interval)
        
        last_heartbeat = 0
        heartbeat_interval = 30
        
        while self._running:
            now = time.time()
            if now - last_heartbeat > heartbeat_interval:
                self.heartbeat(status="IDLE" if not self.current_workflow_id else "BUSY")
                last_heartbeat = now
                
            work = self.check_for_work()
            if work:
                self.execute_work(work)
            else:
                time.sleep(self.poll_interval)
                
    def stop(self):
        self._running = False
        self.heartbeat(status="DRAINING")
        logger.info("worker_stopping")

class CloudWorkerNode(BaseWorkerNode):
    def __init__(self, orchestrator: OrchestratorEngine, control_plane_url: str, worker_id: str, token: str):
        super().__init__(control_plane_url, worker_id, token, "CLOUD")
        self.orchestrator = orchestrator
        # Default cloud capabilities
        self.capabilities = ["coding", "research", "terminal", "browser"]
        self.compute_mode = "CLOUD"

class LaptopWorkerNode(BaseWorkerNode):
    def __init__(self, orchestrator: OrchestratorEngine, control_plane_url: str, worker_id: str, token: str):
        super().__init__(control_plane_url, worker_id, token, "LAPTOP")
        self.orchestrator = orchestrator
        self.capabilities = ["coding", "terminal", "local_model", "ollama"]
        self.compute_mode = "LOCAL"

    def register(self):
        # Additional checks for Ollama health could go here before registering
        super().register()
