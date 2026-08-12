from evoforge.agents.adapters import LegacyAgentAdapter
from evoforge.agents.capabilities import AgentCapability
from evoforge.agents.contracts import AgentContract
from evoforge.agents.registry import AgentRegistry

from evoforge.agents.core.developer import DeveloperAgent
from evoforge.agents.core.qa import QAAgent
from evoforge.agents.core.reviewer import ReviewerAgent
from evoforge.agents.core.security import SecurityAgent

from evoforge.agents.advanced.architect import ArchitectAgent
from evoforge.agents.advanced.conflict_resolver import ConflictResolverAgent
from evoforge.agents.advanced.devops import DevOpsAgent
from evoforge.agents.advanced.documentation import DocumentationAgent
from evoforge.agents.advanced.planner import PlannerAgent
from evoforge.agents.advanced.research import ResearchAgent


def build_agent_registry(router, tools) -> AgentRegistry:
    registry = AgentRegistry()
    
    # 1. Developer
    dev_agent = DeveloperAgent(router, tools)
    dev_contract = AgentContract(
        agent_id="developer",
        name="Developer",
        display_name="Developer Agent",
        role="Write, edit, and refactor code.",
        description="Implements features and fixes bugs.",
        version="1.0.0",
        capabilities=[AgentCapability.CODING, AgentCapability.REFACTORING, AgentCapability.TERMINAL]
    )
    registry.register(dev_contract, LegacyAgentAdapter(dev_contract, dev_agent))
    
    # 2. QA
    qa_agent = QAAgent(router, tools)
    qa_contract = AgentContract(
        agent_id="qa",
        name="QA",
        display_name="QA Agent",
        role="Quality Assurance.",
        description="Writes automated tests and validates code.",
        version="1.0.0",
        capabilities=[AgentCapability.TESTING, AgentCapability.TEST_GENERATION]
    )
    registry.register(qa_contract, LegacyAgentAdapter(qa_contract, qa_agent))
    
    # 3. Reviewer
    rev_agent = ReviewerAgent(router, tools)
    rev_contract = AgentContract(
        agent_id="reviewer",
        name="Reviewer",
        display_name="Code Reviewer",
        role="Reviewer",
        description="Reviews code changes and enforces style.",
        version="1.0.0",
        capabilities=[AgentCapability.CODE_REVIEW]
    )
    registry.register(rev_contract, LegacyAgentAdapter(rev_contract, rev_agent))
    
    # 4. Security
    sec_agent = SecurityAgent(router, tools)
    sec_contract = AgentContract(
        agent_id="security",
        name="Security",
        display_name="Security Auditor",
        role="Security",
        description="Audits code for vulnerabilities.",
        version="1.0.0",
        capabilities=[AgentCapability.SECURITY_ANALYSIS]
    )
    registry.register(sec_contract, LegacyAgentAdapter(sec_contract, sec_agent))
    
    # 5. Architect
    arch_agent = ArchitectAgent(router, tools)
    arch_contract = AgentContract(
        agent_id="architect",
        name="Architect",
        display_name="System Architect",
        role="Architect",
        description="Designs system architecture.",
        version="1.0.0",
        capabilities=[AgentCapability.ARCHITECTURE, AgentCapability.PLANNING]
    )
    registry.register(arch_contract, LegacyAgentAdapter(arch_contract, arch_agent))
    
    # 6. DevOps
    devops_agent = DevOpsAgent(router, tools)
    devops_contract = AgentContract(
        agent_id="devops",
        name="DevOps",
        display_name="DevOps Engineer",
        role="DevOps",
        description="Manages deployment and infrastructure.",
        version="1.0.0",
        capabilities=[AgentCapability.SHELL_EXECUTION]
    )
    registry.register(devops_contract, LegacyAgentAdapter(devops_contract, devops_agent))
    
    # 7. Documentation
    docs_agent = DocumentationAgent(router, tools)
    docs_contract = AgentContract(
        agent_id="documentation",
        name="Documentation",
        display_name="Technical Writer",
        role="Documentation",
        description="Writes and updates documentation.",
        version="1.0.0",
        capabilities=[AgentCapability.DOCUMENTATION]
    )
    registry.register(docs_contract, LegacyAgentAdapter(docs_contract, docs_agent))
    
    # 8. Planner
    plan_agent = PlannerAgent(router, tools)
    plan_contract = AgentContract(
        agent_id="planner",
        name="Planner",
        display_name="Project Planner",
        role="Planner",
        description="Plans out tasks and milestones.",
        version="1.0.0",
        capabilities=[AgentCapability.PLANNING]
    )
    registry.register(plan_contract, LegacyAgentAdapter(plan_contract, plan_agent))
    
    # 9. Research
    res_agent = ResearchAgent(router, tools)
    res_contract = AgentContract(
        agent_id="research",
        name="Research",
        display_name="Researcher",
        role="Research",
        description="Conducts research on new technologies.",
        version="1.0.0",
        capabilities=[AgentCapability.RESEARCH, AgentCapability.BROWSER]
    )
    registry.register(res_contract, LegacyAgentAdapter(res_contract, res_agent))
    
    # 10. Conflict Resolver
    # NOTE: ConflictResolver agent signature is different, it needs evolution_engine.
    # But usually it's initialized with router and tools like others according to tests.
    try:
        conf_agent = ConflictResolverAgent(router, tools, None) # Evolution framework None for now
        conf_contract = AgentContract(
            agent_id="conflict_resolver",
            name="Conflict Resolver",
            display_name="Conflict Resolver",
            role="Conflict Resolver",
            description="Resolves git and logical conflicts.",
            version="1.0.0",
            capabilities=[AgentCapability.REASONING]
        )
        registry.register(conf_contract, LegacyAgentAdapter(conf_contract, conf_agent))
    except Exception:
        pass
    
    return registry
