export interface TraceSummary {
	runId: string;
	caseId: string;
	taskType: string;
	status: string;
	prompt: string;
}

export interface TraceNodeData {
	label: string;
	agentId: string;
	agentRole: string;
	status: string;
	nodeType: string;
	timestamp: string;
	durationMs: number | null;
	payload: Record<string, unknown>;
	component: string;
	taskType: string;
}

export interface TraceFlowData {
	runId: string;
	taskType: string;
	status: string;
	prompt: string;
	finalOutput: string;
	expected: unknown;
	failureCategory: string;
	nodes: Array<{
		id: string;
		type: string;
		position: { x: number; y: number };
		data: TraceNodeData;
	}>;
	edges: Array<{
		id: string;
		source: string;
		target: string;
		style: string;
		animated: boolean;
	}>;
}
