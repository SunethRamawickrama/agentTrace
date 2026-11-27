<script lang="ts">
	import {
		SvelteFlow,
		Controls,
		MiniMap,
		Background,
		BackgroundVariant,
		type Node,
		type Edge
	} from '@xyflow/svelte';
	import '@xyflow/svelte/dist/style.css';

	import AgentNode from './nodes/AgentNode.svelte';
	import LlmCallNode from './nodes/LlmCallNode.svelte';
	import ToolCallNode from './nodes/ToolCallNode.svelte';
	import ErrorNode from './nodes/ErrorNode.svelte';
	import NodeDetail from './NodeDetail.svelte';
	import type { TraceFlowData, TraceNodeData } from '#lib/types';

	let { traceData }: { traceData: TraceFlowData } = $props();

	const nodeTypes = {
		agent: AgentNode,
		llm_call: LlmCallNode,
		tool_call: ToolCallNode,
		error: ErrorNode
	};

	let nodes = $state.raw<Node[]>(traceData.nodes as Node[]);
	let edges = $state.raw<Edge[]>(traceData.edges as Edge[]);
	let selectedNode: TraceNodeData | null = $state(null);
</script>

<div class="flex h-full">
	<div class="flex-1">
		<SvelteFlow
			{nodes}
			{edges}
			{nodeTypes}
			fitView
			onnodeclick={(event) => {
				selectedNode = event.node.data as TraceNodeData;
			}}
			colorMode="dark"
		>
			<Controls />
			<MiniMap />
			<Background variant={BackgroundVariant.Dots} gap={16} size={1} />
		</SvelteFlow>
	</div>
	{#if selectedNode}
		<NodeDetail data={selectedNode} onClose={() => (selectedNode = null)} />
	{/if}
</div>
