<script lang="ts">
	import TraceList from '#lib/components/TraceList.svelte';
	import type { TraceSummary } from '#lib/types';

	let { data } = $props();

	let statusFilter = $state('');
	let taskTypeFilter = $state('');

	let filtered = $derived.by(() => {
		let result: TraceSummary[] = data.traces;
		if (statusFilter) result = result.filter((t) => t.status === statusFilter);
		if (taskTypeFilter) result = result.filter((t) => t.taskType === taskTypeFilter);
		return result;
	});

	let statuses = $derived([...new Set(data.traces.map((t: TraceSummary) => t.status))].sort());
	let taskTypes = $derived([...new Set(data.traces.map((t: TraceSummary) => t.taskType))].sort());
</script>

<div class="p-6">
	<div class="mb-6 flex items-center gap-4">
		<h1 class="text-2xl font-bold text-slate-100">Traces</h1>
		<span class="text-sm text-slate-500">{filtered.length} of {data.traces.length}</span>
	</div>

	<div class="mb-4 flex gap-4">
		<select
			bind:value={statusFilter}
			class="rounded bg-slate-800 border border-slate-700 px-3 py-1.5 text-sm text-slate-200"
		>
			<option value="">All statuses</option>
			{#each statuses as s}
				<option value={s}>{s}</option>
			{/each}
		</select>

		<select
			bind:value={taskTypeFilter}
			class="rounded bg-slate-800 border border-slate-700 px-3 py-1.5 text-sm text-slate-200"
		>
			<option value="">All task types</option>
			{#each taskTypes as t}
				<option value={t}>{t}</option>
			{/each}
		</select>
	</div>

	<TraceList traces={filtered} />
</div>
