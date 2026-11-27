<script lang="ts">
	let { status }: { status: string } = $props();
</script>

<span
	class="inline-block rounded-full px-2.5 py-0.5 text-xs font-medium
		{status === 'pass' ? 'bg-green-900/60 text-green-300' : 'bg-red-900/60 text-red-300'}"
>
	{status}
</span>
