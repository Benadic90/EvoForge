import pytest
from evoforge.evolution.pipeline import EvolutionPipeline
from evoforge.learning.models import EvolutionProposal, Hypothesis, ApprovalPolicy
from evoforge.evolution.experiment import ExperimentFramework, MultiMetricScore, ExperimentRecord
from evoforge.evolution.rollback import RollbackManager
from evoforge.policy_engine.validator import CandidateSecurityGate
from evoforge.memory.database import Database
from evoforge.learning.skill_registry import SkillRegistry
from evoforge.learning.sandbox import SandboxEnvironment
from evoforge.memory.obsidian import ObsidianManager
from evoforge.utils.config import load_config
import os
import uuid

@pytest.fixture
def test_db(tmp_path):
    db_path = str(tmp_path / "test_evo.db")
    db = Database(db_path)
    yield db
    if os.path.exists(db_path):
        os.remove(db_path)

@pytest.fixture
def evolution_pipeline(test_db, tmp_path):
    policy = ApprovalPolicy(risk_level="LOW", requires_human=True, minimum_samples=1, minimum_improvement=0.05, maximum_regression=0.0)
    obsidian = ObsidianManager(str(tmp_path / "obsidian"))
    registry = SkillRegistry(test_db, obsidian)
    framework = ExperimentFramework(test_db, policy)
    env = SandboxEnvironment(str(tmp_path / "sandbox"))
    rollback = RollbackManager(test_db, registry)
    pipeline = EvolutionPipeline(test_db, framework, rollback, policy)
    return pipeline

def test_evolution_proposal_security_gate(evolution_pipeline, test_db):
    proposal = EvolutionProposal(
        proposal_id=str(uuid.uuid4()),
        target_type="PROMPT",
        target_id="agent:dev",
        description="Test",
        candidate_version="disable Policy Engine",
        hypothesis=Hypothesis(
            current_behavior="a", observed_weakness="b", proposed_change="c", expected_improvement="d",
            risk="LOW", benchmark="x", acceptance_threshold="y"
        )
    )
    
    with pytest.raises(ValueError, match="Security Gate Failed"):
        evolution_pipeline.evaluate_proposal(
            proposal, "test_data", [1,2,3], 
            variant_a=lambda x: x, variant_b=lambda x: x,
            evaluator=lambda x: MultiMetricScore(quality=1.0)
        )
    
    rows = test_db.fetchall("SELECT status FROM evolution_proposals WHERE proposal_id = ?", (proposal.proposal_id,))
    # Might not be saved in db yet if not proposed through agent, but let's assume it was saved before.
    # We should actually test CandidateSecurityGate independently.

def test_security_gate_standalone():
    gate = CandidateSecurityGate()
    is_safe, reason = gate.validate_proposal("PROMPT", "this has unrestricted shell access")
    assert not is_safe
    assert "Forbidden keyword" in reason
    
    is_safe, reason = gate.validate_proposal("SKILL", "aws_secret = 'AKIAIOSFODNN7EXAMPLE'")
    assert not is_safe
    assert "Hardcoded secrets" in reason
    
    is_safe, reason = gate.validate_proposal("SKILL", "print('hello world')")
    assert is_safe

def test_evolution_pipeline_success(evolution_pipeline, test_db):
    proposal = EvolutionProposal(
        proposal_id=str(uuid.uuid4()),
        target_type="SKILL",
        target_id="agent:dev",
        description="Test improvement",
        candidate_version="clean code",
        hypothesis=Hypothesis(
            current_behavior="a", observed_weakness="b", proposed_change="c", expected_improvement="d",
            risk="LOW", benchmark="x", acceptance_threshold="y"
        )
    )
    test_db.execute(
        "INSERT INTO evolution_proposals (proposal_id, target_type, target_id) VALUES (?, ?, ?)",
        (proposal.proposal_id, proposal.target_type, proposal.target_id)
    )
    
    def variant_a(data):
        return data
        
    def variant_b(data):
        return data + 10 # Better
        
    def evaluator(res):
        return MultiMetricScore(quality=res)
        
    record = evolution_pipeline.evaluate_proposal(
        proposal, "test_dataset", [10, 20],
        variant_a=variant_a, variant_b=variant_b,
        evaluator=evaluator
    )
    
    assert record.status == "PASSED"
    assert record.improvement_percent > 0
    
    rows = test_db.fetchall("SELECT status FROM evolution_proposals WHERE proposal_id = ?", (proposal.proposal_id,))
    assert rows[0]["status"] == "PASSED" # pending human approval

def test_rollback(evolution_pipeline, test_db):
    proposal_id = str(uuid.uuid4())
    test_db.execute(
        "INSERT INTO evolution_proposals (proposal_id, target_type, target_id, rollback_version, status) VALUES (?, ?, ?, ?, ?)",
        (proposal_id, "SKILL", "agent1:skill1", "1", "DEPLOYED")
    )
    test_db.execute(
        "INSERT INTO evolution_deployments (deployment_id, proposal_id, deployed_version, rollback_version, status) VALUES (?, ?, ?, ?, ?)",
        ("dep1", proposal_id, "2", "1", "ACTIVE")
    )
    test_db.execute(
        "INSERT INTO skills (id, agent_name, skill_name, version, metadata, capability_level, confidence) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("skill_id_123", "agent1", "skill1", 2, "{}", "BEGINNER", 0.5)
    )
    skill_id = "skill_id_123"
    test_db.execute(
        "INSERT INTO skill_versions (skill_id, version, system_prompt_patch, techniques, tools, patterns, anti_patterns, benchmark_score) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (skill_id, 1, "", "[]", "[]", "[]", "[]", 0.0)
    )
    
    success = evolution_pipeline.rollback_manager.rollback_proposal(proposal_id)
    assert success
    
    p_rows = test_db.fetchall("SELECT status FROM evolution_proposals WHERE proposal_id = ?", (proposal_id,))
    assert p_rows[0]["status"] == "ROLLED_BACK"
    
    d_rows = test_db.fetchall("SELECT status FROM evolution_deployments WHERE deployment_id = ?", ("dep1",))
    assert d_rows[0]["status"] == "ROLLED_BACK"
