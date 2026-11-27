<script lang="ts">
	import type { TraceNodeData } from '#lib/types';

	let { data, onClose }: { data: TraceNodeData; onClose: () => void } = $props();
</script>

<div class="w-96 border-l border-slate-700 bg-slate-900 p-4 overflow-y-auto h-full">
	<div class="flex items-center justify-between mb-4">
		<h3 class="text-lg font-semibold text-slate-100">Node Detail</h3>
		<button onclick={onClose} class="text-slate-400 hover:text-slate-200 text-xl cursor-pointer">&times;</button>
	</div>

	<div class="space-y-3 text-sm">
		<div>
			<span class="text-slate-400">Label:</span>
			<span class="text-slate-100 ml-1">{data.label}</span>
		</div>
		<div>
			<span class="text-slate-400">Type:</span>
			<span class="text-slate-100 ml-1">{data.nodeType}</span>
		</div>
		<div>
			<span class="text-slate-400">Agent:</span>
			<span class="text-slate-100 ml-1">{data.agentId}</span>
		</div>
		<div>
			<span class="text-slate-400">Role:</span>
			<span class="text-slate-100 ml-1">{data.agentRole}</span>
		</div>
		<div>
			<span class="text-slate-400">Status:</span>
			<span class="ml-1 {data.status === 'failed' ? 'text-red-400' : 'text-green-400'}">{data.status}</span>
		</div>
		<div>
			<span class="text-slate-400">Component:</span>
			<span class="text-slate-100 ml-1">{data.component}</span>
		</div>
		<div>
			<span class="text-slate-400">Timestamp:</span>
			<span class="text-slate-100 ml-1">{data.timestamp}</span>
		</div>
		{#if data.durationMs}
			<div>
				<span class="text-slate-400">Duration:</span>
				<span class="text-slate-100 ml-1">{data.durationMs}ms</span>
			</div>
		{/if}

		<div class="pt-2 border-t border-slate-700">
			<div class="text-slate-400 mb-1">Payload:</div>
			<pre class="bg-slate-950 rounded p-2 text-xs text-slate-300 overflow-x-auto max-h-80 overflow-y-auto">{JSON.stringify(data.payload, null, 2)}</pre>
		</div>
	</div>
</div>
