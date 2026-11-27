<script lang="ts">
	import type { TraceSummary } from '#lib/types';
	import StatusBadge from './StatusBadge.svelte';

	let { traces }: { traces: TraceSummary[] } = $props();
</script>

<div class="overflow-x-auto">
	<table class="w-full text-sm text-left">
		<thead class="text-xs uppercase text-slate-400 border-b border-slate-700">
			<tr>
				<th class="px-4 py-3">Case ID</th>
				<th class="px-4 py-3">Task Type</th>
				<th class="px-4 py-3">Status</th>
				<th class="px-4 py-3">Prompt</th>
			</tr>
		</thead>
		<tbody>
			{#each traces as trace}
				<tr class="border-b border-slate-800 hover:bg-slate-800/50">
					<td class="px-4 py-3">
						<a href="/traces/{trace.runId}" class="text-blue-400 hover:text-blue-300 hover:underline">
							{trace.caseId}
						</a>
					</td>
					<td class="px-4 py-3 text-slate-300">{trace.taskType}</td>
					<td class="px-4 py-3"><StatusBadge status={trace.status} /></td>
					<td class="px-4 py-3 text-slate-400 max-w-md truncate">{trace.prompt}</td>
				</tr>
			{/each}
		</tbody>
	</table>
</div>
