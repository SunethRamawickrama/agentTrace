<script lang="ts">
	import { Handle, Position, type NodeProps } from '@xyflow/svelte';

	let { data }: NodeProps = $props();
</script>

<Handle type="target" position={Position.Top} />
<div
	class="rounded-lg border-2 px-4 py-2 shadow-md min-w-[160px] text-center
		{data.status === 'failed' ? 'border-red-500 bg-red-950/60' : 'border-purple-500 bg-purple-950/60'}"
>
	<div class="text-sm font-semibold text-purple-200">{data.label}</div>
	{#if data.durationMs}
		<div class="text-xs text-slate-400">{data.durationMs}ms</div>
	{/if}
</div>
<Handle type="source" position={Position.Bottom} />
