import pytest
import os
from unittest.mock import MagicMock, patch
from evoforge.runtime.scheduler import SchedulerEngine
from evoforge.github_integration.client import GitHubClient
from evoforge.memory.database import Database

@pytest.fixture
def mock_db():
    db = MagicMock(spec=Database)
    db.fetchall.return_value = []
    return db

def test_scheduler_valid_github_client(mock_db):
    """1. Scheduler with valid GitHubClient"""
    gh_client = MagicMock()
    gh_client.token = "valid_token"
    
    scheduler = SchedulerEngine(mock_db, gh_client)
    
    with patch.object(scheduler, 'enqueue_portfolio_tasks') as mock_enqueue, \
         patch.object(scheduler, 'execute_pending_workflows') as mock_execute:
         
         scheduler.run_once()
         
         # With valid token, it should proceed to enqueue tasks
         mock_enqueue.assert_called_once()

def test_scheduler_missing_github_credentials(mock_db):
    """2. Scheduler with missing GitHub credentials"""
    gh_client = MagicMock()
    gh_client.token = None  # No token
    
    scheduler = SchedulerEngine(mock_db, gh_client)
    
    with patch.object(scheduler, 'enqueue_portfolio_tasks') as mock_enqueue:
         scheduler.run_once()
         
         # With no token, it should abort tick and log GITHUB_UNAVAILABLE
         mock_enqueue.assert_not_called()

def test_github_client_transient_failure(mock_db):
    """3. GitHub client transient failure"""
    gh_client = MagicMock()
    gh_client.token = "valid_token"
    
    scheduler = SchedulerEngine(mock_db, gh_client)
    
    # Simulate transient network failure during scan
    with patch.object(scheduler, 'enqueue_portfolio_tasks', side_effect=Exception("Connection reset by peer")) as mock_enqueue, \
         patch.object(scheduler, '_update_state') as mock_update:
         
         scheduler.run_once()
         
         mock_enqueue.assert_called_once()
         
         # It should catch the exception and update state with last_failure
         call_args_list = mock_update.call_args_list
         assert any("last_failure" in kwargs for args, kwargs in call_args_list)

def test_api_remains_healthy_when_scheduler_dependency_fails(mock_db):
    """4. API remains healthy when scheduler dependency fails"""
    # Simply initializing the components should not raise an exception
    with patch.dict(os.environ, {}, clear=True):
        gh_client = GitHubClient(db=mock_db)
        # Verify it doesn't crash on init
        scheduler = SchedulerEngine(mock_db, gh_client)
        assert scheduler.gh_client is gh_client

def test_scheduler_retries_later(mock_db):
    """5. Scheduler retries later"""
    gh_client = MagicMock()
    gh_client.token = "valid_token"
    
    scheduler = SchedulerEngine(mock_db, gh_client)
    
    # First tick fails
    with patch.object(scheduler, 'enqueue_portfolio_tasks', side_effect=Exception("Network error")):
         scheduler.run_once()
         
    # Second tick succeeds
    with patch.object(scheduler, 'enqueue_portfolio_tasks') as mock_enqueue:
         scheduler.run_once()
         mock_enqueue.assert_called_once()
