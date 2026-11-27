<script lang="ts">
	import TraceGraph from '#lib/components/TraceGraph.svelte';
	import StatusBadge from '#lib/components/StatusBadge.svelte';

	let { data } = $props();
	let trace = data.trace;
</script>

<div class="flex flex-col h-[calc(100vh-49px)]">
	<div class="border-b border-slate-800 bg-slate-900 px-6 py-3">
		<div class="flex items-center gap-4 mb-1">
			<a href="/traces" class="text-sm text-slate-500 hover:text-slate-300">&larr; Back</a>
			<h2 class="text-lg font-semibold text-slate-100">{trace.taskType}</h2>
			<StatusBadge status={trace.status} />
			{#if trace.failureCategory && trace.failureCategory !== 'pass'}
				<span class="text-xs text-orange-400">{trace.failureCategory}</span>
			{/if}
		</div>
		<div class="flex gap-6 text-xs text-slate-500">
			<span>Run: {trace.runId.slice(0, 8)}&hellip;</span>
			<span>Expected: {JSON.stringify(trace.expected)}</span>
			<span class="max-w-lg truncate">Output: {trace.finalOutput}</span>
		</div>
	</div>

	<div class="flex-1">
		<TraceGraph traceData={trace} />
	</div>
</div>
