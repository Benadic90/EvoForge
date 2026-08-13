import React, { useState, useEffect } from 'react';

const EvolutionView = () => {
    const [proposals, setProposals] = useState([]);
    const [experiments, setExperiments] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [propRes, expRes] = await Promise.all([
                fetch('/api/evolution/proposals'),
                fetch('/api/evolution/experiments')
            ]);
            if (propRes.ok) {
                const p = await propRes.json();
                setProposals(p);
            }
            if (expRes.ok) {
                const e = await expRes.json();
                setExperiments(e);
            }
        } catch (error) {
            console.error('Failed to fetch evolution data:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 10000);
        return () => clearInterval(interval);
    }, []);

    const getStatusColor = (status) => {
        switch (status) {
            case 'PASSED': return 'text-emerald-400 border-emerald-400/20 bg-emerald-400/10';
            case 'APPROVED': return 'text-blue-400 border-blue-400/20 bg-blue-400/10';
            case 'DEPLOYED': return 'text-purple-400 border-purple-400/20 bg-purple-400/10';
            case 'FAILED': return 'text-red-400 border-red-400/20 bg-red-400/10';
            case 'ROLLED_BACK': return 'text-orange-400 border-orange-400/20 bg-orange-400/10';
            default: return 'text-zinc-400 border-zinc-700 bg-zinc-800/50';
        }
    };

    if (loading && proposals.length === 0) {
        return <div className="p-8 text-zinc-400">Loading Controlled Evolution Data...</div>;
    }

    return (
        <div className="p-8 space-y-8 animate-in fade-in duration-500">
            <header className="mb-8 border-b border-zinc-800 pb-6">
                <h1 className="text-3xl font-light tracking-tight text-zinc-100">Self-Evolution</h1>
                <p className="text-zinc-400 mt-2 text-lg">Controlled evolution pipelines and A/B test results</p>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Proposals Column */}
                <div className="space-y-4">
                    <h2 className="text-xl font-medium text-zinc-100 flex items-center gap-2">
                        Evolution Proposals
                        <span className="text-xs bg-zinc-800 text-zinc-400 px-2 py-1 rounded-full">{proposals.length}</span>
                    </h2>
                    
                    {proposals.length === 0 ? (
                        <div className="p-8 border border-dashed border-zinc-800 rounded-xl text-center text-zinc-500">
                            No active proposals.
                        </div>
                    ) : (
                        proposals.map(p => {
                                const handleApprove = async (proposalId) => {
                                    try {
                                        const res = await fetch(`/api/evolution/proposals/${proposalId}/approve`, {
                                            method: 'POST',
                                            headers: { 'Content-Type': 'application/json' },
                                            body: JSON.stringify({ deployment_type: 'FULL' })
                                        });
                                        if (res.ok) fetchData();
                                    } catch (e) {
                                        console.error(e);
                                    }
                                };
                                const handleReject = async (proposalId) => {
                                    try {
                                        const res = await fetch(`/api/evolution/proposals/${proposalId}/reject`, { method: 'POST' });
                                        if (res.ok) fetchData();
                                    } catch (e) {
                                        console.error(e);
                                    }
                                };
                                return (
                            <div key={p.proposal_id} className="bg-zinc-900/50 border border-zinc-800/50 p-5 rounded-xl hover:bg-zinc-800/30 transition-colors">
                                <div className="flex justify-between items-start mb-3">
                                    <div>
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="text-xs font-mono text-zinc-500">{p.proposal_id.substring(0,8)}</span>
                                            <span className={`text-xs px-2 py-0.5 rounded-full border ${getStatusColor(p.status)}`}>
                                                {p.status}
                                            </span>
                                        </div>
                                        <h3 className="text-zinc-100 font-medium">{p.target_type}: {p.target_id}</h3>
                                    </div>
                                </div>
                                <p className="text-sm text-zinc-400 mb-4">{p.description}</p>
                                
                                {p.hypothesis && (
                                    <div className="bg-black/20 p-3 rounded-lg border border-zinc-800/30 mb-4 text-xs space-y-2">
                                        <div className="flex justify-between">
                                            <span className="text-zinc-500">Weakness:</span>
                                            <span className="text-zinc-300 text-right">{p.hypothesis.observed_weakness}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-zinc-500">Proposed Change:</span>
                                            <span className="text-zinc-300 text-right">{p.hypothesis.proposed_change}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-zinc-500">Expected:</span>
                                            <span className="text-emerald-400/80 text-right">{p.hypothesis.expected_improvement}</span>
                                        </div>
                                    </div>
                                )}
                                
                                <div className="flex gap-2">
                                    {p.status === 'PASSED' && (
                                        <>
                                            <button onClick={() => handleApprove(p.proposal_id)} className="px-3 py-1.5 text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-md hover:bg-emerald-500/20 transition-colors">
                                                Approve
                                            </button>
                                            <button onClick={() => handleReject(p.proposal_id)} className="px-3 py-1.5 text-xs bg-red-500/10 text-red-400 border border-red-500/20 rounded-md hover:bg-red-500/20 transition-colors">
                                                Reject
                                            </button>
                                        </>
                                    )}
                                    {p.status === 'APPROVED' && (
                                        <button className="px-3 py-1.5 text-xs bg-purple-500/10 text-purple-400 border border-purple-500/20 rounded-md hover:bg-purple-500/20 transition-colors">
                                            Deploy CANARY
                                        </button>
                                    )}
                                </div>
                            </div>
                            );
                        })
                    )}
                </div>

                {/* Experiments Column */}
                <div className="space-y-4">
                    <h2 className="text-xl font-medium text-zinc-100 flex items-center gap-2">
                        Benchmark Experiments
                        <span className="text-xs bg-zinc-800 text-zinc-400 px-2 py-1 rounded-full">{experiments.length}</span>
                    </h2>

                    {experiments.length === 0 ? (
                        <div className="p-8 border border-dashed border-zinc-800 rounded-xl text-center text-zinc-500">
                            No active experiments.
                        </div>
                    ) : (
                        experiments.map(e => (
                            <div key={e.experiment_id} className="bg-zinc-900/50 border border-zinc-800/50 p-5 rounded-xl hover:bg-zinc-800/30 transition-colors">
                                <div className="flex justify-between items-start mb-3">
                                    <div>
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="text-xs font-mono text-zinc-500">{e.experiment_id.substring(0,8)}</span>
                                            <span className={`text-xs px-2 py-0.5 rounded-full border ${e.status === 'PASSED' ? 'text-emerald-400 border-emerald-400/20 bg-emerald-400/10' : e.status === 'FAILED' ? 'text-red-400 border-red-400/20 bg-red-400/10' : 'text-blue-400 border-blue-400/20 bg-blue-400/10'}`}>
                                                {e.status}
                                            </span>
                                        </div>
                                        <h3 className="text-zinc-100 font-medium">Proposal: {e.proposal_id.substring(0,8)}</h3>
                                    </div>
                                </div>
                                
                                <div className="grid grid-cols-2 gap-4 text-sm mt-4">
                                    <div className="bg-black/20 p-3 rounded-lg border border-zinc-800/30 text-center">
                                        <div className="text-zinc-500 text-xs mb-1">Improvement</div>
                                        <div className={`text-xl font-light ${e.improvement_percent > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                            {(e.improvement_percent * 100).toFixed(1)}%
                                        </div>
                                    </div>
                                    <div className="bg-black/20 p-3 rounded-lg border border-zinc-800/30 text-center">
                                        <div className="text-zinc-500 text-xs mb-1">Regressions</div>
                                        <div className={`text-xl font-light ${e.regressions === 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                            {e.regressions}
                                        </div>
                                    </div>
                                    <div className="bg-black/20 p-3 rounded-lg border border-zinc-800/30 text-center">
                                        <div className="text-zinc-500 text-xs mb-1">Samples</div>
                                        <div className="text-zinc-300 text-xl font-light">{e.sample_count}</div>
                                    </div>
                                    <div className="bg-black/20 p-3 rounded-lg border border-zinc-800/30 text-center">
                                        <div className="text-zinc-500 text-xs mb-1">Target</div>
                                        <div className="text-zinc-300 text-sm truncate" title={e.target}>{e.target}</div>
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};

export default EvolutionView;
