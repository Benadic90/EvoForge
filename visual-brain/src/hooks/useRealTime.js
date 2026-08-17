import { useState, useEffect, useRef } from 'react';
import { api } from '../api/client';

export function useRealTime(pollingIntervalMs = 3000) {
  const [status, setStatus] = useState({
    system: null,
    runtime: null,
    scheduler: null,
    isOffline: false,
    lastUpdate: null
  });
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  // Store a ref to avoid stale closure issues in the interval
  const stateRef = useRef({ lastEventId: null });

  const fetchLoop = async () => {
    try {
      const [sysRes, runRes, schedRes, evRes] = await Promise.all([
        api.getSystemStatus(),
        api.getRuntimeStatus(),
        api.getSchedulerStatus(),
        api.getRecentEvents()
      ]);

      setStatus({
        system: sysRes,
        runtime: runRes,
        scheduler: schedRes,
        isOffline: false,
        lastUpdate: new Date()
      });

      setEvents(evRes || []);
    } catch (err) {
      console.warn("RealTime polling failed, backend may be offline:", err);
      setStatus(prev => ({ ...prev, isOffline: true }));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Initial fetch
    fetchLoop();
    
    // Polling interval
    const intervalId = setInterval(fetchLoop, pollingIntervalMs);
    
    return () => clearInterval(intervalId);
  }, [pollingIntervalMs]);

  return {
    ...status,
    events,
    loading
  };
}
