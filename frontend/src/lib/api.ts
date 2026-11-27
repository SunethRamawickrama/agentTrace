import type { TraceSummary, TraceFlowData } from './types';

export async function fetchTraces(
	status?: string,
	taskType?: string
): Promise<TraceSummary[]> {
	const params = new URLSearchParams();
	if (status) params.set('status', status);
	if (taskType) params.set('task_type', taskType);

	const qs = params.toString();
	const res = await fetch(`/api/traces${qs ? '?' + qs : ''}`);
	const data = await res.json();
	return data.traces;
}

export async function fetchTrace(runId: string): Promise<TraceFlowData> {
	const res = await fetch(`/api/traces/${runId}`);
	if (!res.ok) throw new Error('Trace not found');
	return res.json();
}
